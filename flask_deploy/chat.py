import requests
import subprocess
import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import re  # 新增正则模块，用于处理Markdown符号
from dotenv import load_dotenv  # 修正导入语句
load_dotenv()


# ==================== 配置区域 ====================
class Config:
    API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.siliconflow.cn/v1/chat/completions")
    API_KEY = os.environ.get("SILICONFLOW_API_KEY")  # 从环境变量获取，必填


config = Config()

# 验证必要配置
if not config.API_KEY:
    logging.error("API_KEY未设置，请通过环境变量SILICONFLOW_API_KEY设置")
    exit(1)
# =================================================

# 初始化日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)
CORS(app)  # 允许跨域请求


def clean_markdown(content):
    """清理Markdown格式符号（###、**、*、`等）"""
    if not content:
        return ""
    # 移除Markdown标题符号（#）
    content = re.sub(r'^#{1,6}\s+', '', content, flags=re.MULTILINE)
    # 移除加粗/斜体符号（**、*）
    content = re.sub(r'\*\*', '', content)
    content = re.sub(r'\*', '', content)
    # 移除代码块符号（`）
    content = re.sub(r'`', '', content)
    # 移除列表符号（-、*、+）
    content = re.sub(r'^[-\*\+]\s+', '', content, flags=re.MULTILINE)
    # 移除多余空行
    content = re.sub(r'\n{3,}', '\n\n', content)
    return content.strip()


def generate_code(user_input, deep_think=False, model=None):
    """调用硅基流动API生成代码，支持深度思考模式，并清理Markdown符号"""
    if not user_input or len(user_input.strip()) == 0:
        return {"error": "生成失败：用户输入不能为空"}
    # 设置默认模型（如果前端未传递则使用默认）
    selected_model = model if model else "deepseek-ai/DeepSeek-V3"  # 新增
    # 根据深度思考模式调整提示词，明确要求不要Markdown格式
    if deep_think:
        # 构建更详细的提示词，引导模型输出纯文本思考过程（无Markdown）
        prompt = f"""请先详细描述你的思考过程，再给出最终代码。

注意：思考过程和代码都不要使用任何Markdown格式（如#、**、*、`等符号），纯文本描述即可。

用户需求：{user_input.strip()}

请使用思考结束作为思考过程和代码的分隔符。"""
    else:
        prompt = f"{user_input.strip()}\n注意：生成的内容不要使用任何Markdown格式（如#、**、*、`等符号），纯文本输出即可。"

    # 构造请求体
    payload = {
        "model": selected_model,  # 原为 config.MODEL_NAME，改为选中的模型
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    # 请求头
    headers = {
        "Authorization": f"Bearer {config.API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        # 发送POST请求
        response = requests.request(
            "POST",
            url=config.API_BASE_URL,
            json=payload,
            headers=headers,
            timeout=60  # 深度思考可能需要更长时间
        )
        response.raise_for_status()  # 抛出HTTP错误

        # 解析响应
        response_json = response.json()
        logging.info(f"硅基流动API响应：{response_json}")

        # 提取生成的内容
        if "choices" not in response_json or len(response_json["choices"]) == 0:
            return {"error": "生成失败：API返回无有效内容"}

        content = response_json["choices"][0]["message"]["content"].strip()

        # 清理内容中的Markdown符号（双重保险，即使模型返回了也会移除）
        content = clean_markdown(content)

        # 如果是深度思考模式，尝试分离思考过程和代码
        if deep_think:
            # 尝试使用【思考结束】分隔符
            if "思考结束" in content:
                parts = content.split("思考结束", 1)
                thought_process = parts[0].strip()
                code = parts[1].strip()

                # 对思考过程和代码分别再次清理（确保无残留符号）
                thought_process = clean_markdown(thought_process)
                code = clean_markdown(code)

                return {
                    "thought_process": thought_process,
                    "code": code
                }
            else:
                # 如果没有分隔符，整个内容作为代码返回
                logging.warning("深度思考模式未找到分隔符思考结束")
                return {"code": content}
        else:
            # 普通模式直接返回代码（再次清理）
            return {"code": clean_markdown(content)}

    except requests.exceptions.RequestException as e:
        logging.error(f"API请求失败：{str(e)}")
        if 'response' in locals() and hasattr(response, 'text'):
            logging.error(f"API错误响应：{response.text}")
        return {"error": f"生成失败：请求错误 - {str(e)}"}
    except Exception as e:
        logging.error(f"处理响应失败：{str(e)}")
        return {"error": f"生成失败：处理错误 - {str(e)}"}


def check_code_errors(code):
    """调用Pylint检测代码错误"""
    if not code or len(code.strip()) == 0:
        return "检测失败：代码不能为空"

    try:
        # 调用pylint检测错误
        result = subprocess.run(
            ["pylint", "--disable=all", "--enable=error", "-"],
            input=code,
            capture_output=True,
            text=True,
            timeout=15
        )

        if result.stderr:
            logging.warning(f"pylint警告：{result.stderr}")

        errors = result.stdout.strip()
        return errors if errors else "未检测到语法错误"

    except FileNotFoundError:
        return "检测失败：未安装pylint，请执行 'pip install pylint'"
    except subprocess.TimeoutExpired:
        return "检测失败：超时（代码可能过长或复杂）"
    except Exception as e:
        logging.error(f"代码检测错误：{str(e)}")
        return f"检测失败：{str(e)}"


@app.route('/generate', methods=['POST'])
def handle_generate():
    try:
        request_data = request.get_json(silent=True)
        if not request_data or not isinstance(request_data, dict):
            return jsonify({"error": "请求格式错误：请发送JSON数据"}), 400

        user_input = request_data.get("prompt", "").strip()
        deep_think = request_data.get("deep_think", False)
        selected_model = request_data.get("model")  # 新增：获取前端选中的模型

        # 调用生成函数时传递模型参数（修改）
        result = generate_code(user_input, deep_think, selected_model)  # 新增 selected_model 参数

        # 检查是否有错误
        if "error" in result:
            return jsonify(result), 500

        return jsonify(result)

    except Exception as e:
        logging.error(f"生成接口错误：{str(e)}")
        return jsonify({"error": f"接口处理失败 - {str(e)}"}), 500


@app.route('/check_errors', methods=['POST'])
def handle_check_errors():
    try:
        request_data = request.get_json(silent=True)
        if not request_data or not isinstance(request_data, dict):
            return jsonify({"error": "请求格式错误：请发送JSON数据"}), 400

        code = request_data.get("code", "").strip()
        errors = check_code_errors(code)
        return jsonify({"errors": errors})

    except Exception as e:
        logging.error(f"检测接口错误：{str(e)}")
        return jsonify({"error": f"接口处理失败 - {str(e)}"}), 500


if __name__ == '__main__':
    port = int(os.environ.get("FLASK_PORT", 8148))
    from waitress import serve

    logging.info(f"服务启动：http://0.0.0.0:{port}")
    serve(app, host='0.0.0.0', port=port, threads=4)
