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

def generate_problem_prompt():
    # 构造提示词，要求AI生成一个编程题目
    prompt = "请随机生成一个编程题目，要求描述清晰，可实现性强，题目难度适中，且不要使用任何Markdown格式，每次生成的题目要不一样，每次生成的题目涉及编程语言不一样，涉及编程语言有c++，java，python。"
    payload = {
        "model": "deepseek-ai/DeepSeek-V3",  # 可根据需要修改模型
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }
    headers = {
        "Authorization": f"Bearer {config.API_KEY}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.request(
            "POST",
            url=config.API_BASE_URL,
            json=payload,
            headers=headers,
            timeout=60
        )
        response.raise_for_status()
        response_json = response.json()
        if "choices" not in response_json or len(response_json["choices"]) == 0:
            return {"error": "生成失败：API返回无有效内容"}
        content = response_json["choices"][0]["message"]["content"].strip()
        return {"problem": content}
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


def analyze_code_quality(code, problem_description):
    """分析代码质量并提供优化建议"""
    # 构建提示词，结合题目描述和用户代码
    prompt = f"""请分析以下代码的质量并提供优化建议：

题目描述：
{problem_description}

用户代码：
{code}

请从以下几个方面分析：
1. 代码是否正确解决了问题
2. 代码的时间和空间复杂度
3. 代码的可读性和可维护性
4. 代码风格和最佳实践
5. 可能存在的潜在问题
6. 优化建议

请以清晰、简洁的语言回答，避免使用Markdown格式。"""

    # 调用模型分析代码
    result = generate_code(prompt)
    
    if "error" in result:
        return result["error"]
    
    return result["code"]


@app.route('/generate', methods=['POST'])
def handle_generate():
    try:
        request_data = request.get_json(silent=True)
        if not request_data or not isinstance(request_data, dict):
            return jsonify({"error": "请求格式错误：请发送JSON数据"}), 400

        user_input = request_data.get("prompt", "").strip()
        deep_think = request_data.get("deep_think", False)
        selected_model = request_data.get("model")  # 获取前端选中的模型

        # 检查模型是否有效
        valid_models = ["deepseek-ai/DeepSeek-V3", "Tongyi-Zhiwen/QwenLong-L1-32B", "Qwen/Qwen3-30B-A3B"]
        if selected_model not in valid_models:
            selected_model = "deepseek-ai/DeepSeek-V3"  # 使用默认模型
            logging.warning(f"无效的模型选择，使用默认模型: {selected_model}")

        result = generate_code(user_input, deep_think, selected_model)  # 传递选中的模型

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


@app.route('/analyze_file', methods=['POST'])
def handle_analyze_file():
    try:
        request_data = request.get_json(silent=True)
        if not request_data or not isinstance(request_data, dict):
            return jsonify({"error": "请求格式错误：请发送JSON数据"}), 400

        file_content = request_data.get("file_content", "").strip()
        file_extension = request_data.get("file_extension", "").strip()

        # 这里可以添加具体的文件内容分析逻辑
        # 例如，根据文件扩展名调用不同的分析工具
        analysis_result = analyze_file_content(file_content, file_extension)

        return jsonify({"analysis_result": analysis_result})

    except Exception as e:
        logging.error(f"文件分析接口错误：{str(e)}")
        return jsonify({"error": f"接口处理失败 - {str(e)}"}), 500


def analyze_file_content(file_content, file_extension):
    # 简单示例：根据文件扩展名进行不同的处理
    if file_extension == "py":
        # 处理Python文件
        return "Python文件分析结果：...（这里添加具体分析逻辑）"
    elif file_extension == "js":
        # 处理JavaScript文件
        return "JavaScript文件分析结果：...（这里添加具体分析逻辑）"
    else:
        return "不支持的文件类型"


@app.route('/study_summary', methods=['POST'])
def handle_study_summary():
    try:
        request_data = request.get_json(silent=True)
        if not request_data or not isinstance(request_data, dict):
            return jsonify({"error": "请求格式错误：请发送JSON数据"}), 400

        history = request_data.get("chat_history", [])
        today = request_data.get("today", "")

        # 统计今天的OJ系统做题相关对话
        today_sessions = [session for session in history if session.get("time", "").startswith(today)]
        problem_count = 0
        study_topics = []

        for session in today_sessions:
            for msg in session.get("session", []):
                if msg.get("role") == "user" and "OJ 系统提交代码:" in msg.get("content", ""):
                    problem_count += 1
                    # 提取题目相关的内容作为学习主题
                    content = msg.get("content", "")
                    topic = content[content.index("OJ 系统提交代码:") + len("OJ 系统提交代码:"):][:50]
                    if topic not in study_topics:
                        study_topics.append(topic)

        summary = {
            "problem_count": problem_count,
            "study_topics": study_topics
        }

        return jsonify(summary)

    except Exception as e:
        logging.error(f"做题总结接口错误：{str(e)}")
        return jsonify({"error": f"接口处理失败 - {str(e)}"}), 500


@app.route('/generate-problem', methods=['POST'])
def handle_generate_problem():
    try:
        request_data = request.get_json(silent=True)
        if not request_data or not isinstance(request_data, dict):
            return jsonify({"error": "请求格式错误：请发送JSON数据"}), 400

        model = request_data.get("model")  # 获取前端选中的模型

        # 检查模型是否有效
        valid_models = ["deepseek-ai/DeepSeek-V3", "Tongyi-Zhiwen/QwenLong-L1-32B", "Qwen/Qwen3-30B-A3B"]
        if model not in valid_models:
            model = "deepseek-ai/DeepSeek-V3"  # 使用默认模型
            logging.warning(f"无效的模型选择，使用默认模型: {model}")

        # 调用生成题目函数
        result = generate_problem_prompt()

        if "error" in result:
            return jsonify({"error": result["error"]}), 500

        return jsonify(result)

    except Exception as e:
        logging.error(f"生成题目接口错误：{str(e)}")
        return jsonify({"error": f"接口处理失败 - {str(e)}"}), 500


# 新增：处理代码提交的接口
@app.route('/submit-code', methods=['POST'])
def handle_submit_code():
    try:
        request_data = request.get_json(silent=True)
        if not request_data or not isinstance(request_data, dict):
            return jsonify({"error": "请求格式错误：请发送JSON数据"}), 400

        # 获取请求参数
        problem = request_data.get("problem", "").strip()
        user_code = request_data.get("code", "").strip()
        model = request_data.get("model")  # 获取前端选中的模型

        # 检查模型是否有效
        valid_models = ["deepseek-ai/DeepSeek-V3", "Tongyi-Zhiwen/QwenLong-L1-32B", "Qwen/Qwen3-30B-A3B"]
        if model not in valid_models:
            model = "deepseek-ai/DeepSeek-V3"  # 使用默认模型
            logging.warning(f"无效的模型选择，使用默认模型: {model}")

        # 验证参数
        if not problem:
            return jsonify({"error": "题目不能为空"}), 400
        if not user_code:
            return jsonify({"error": "代码不能为空"}), 400

        # 1. 生成参考答案
        logging.info(f"生成参考答案：题目={problem[:50]}...")
        answer_prompt = f"请提供以下问题的标准答案：\n\n{problem}\n\n请确保代码正确且符合最佳实践，不要使用任何Markdown格式。"
        answer_result = generate_code(answer_prompt, model=model)
        
        if "error" in answer_result:
            return jsonify({"error": f"生成参考答案失败：{answer_result['error']}"}), 500
        
        reference_answer = answer_result.get("code", "")
        
        # 2. 分析用户代码
        logging.info(f"分析用户代码：长度={len(user_code)}")
        code_analysis = analyze_code_quality(user_code, problem)
        
        # 3. 检查代码错误
        logging.info("检查代码错误")
        code_errors = check_code_errors(user_code)
        
        # 构建响应
        response_data = {
            "reference_answer": reference_answer,
            "code_analysis": code_analysis,
            "code_errors": code_errors
        }
        
        return jsonify(response_data)

    except Exception as e:
        logging.error(f"提交代码接口错误：{str(e)}")
        return jsonify({"error": f"接口处理失败 - {str(e)}"}), 500


if __name__ == '__main__':
    port = int(os.environ.get("FLASK_PORT", 8148))
    from waitress import serve

    logging.info(f"服务启动：http://0.0.0.0:{port}")
    serve(app, host='0.0.0.0', port=port, threads=4)    