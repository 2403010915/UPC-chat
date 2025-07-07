document.addEventListener('DOMContentLoaded', function() {
    // 常用DOM元素
    const messagesDiv = document.getElementById('messages');
    const input = document.getElementById('input');
    const sendBtn = document.getElementById('send-btn');
    
    // 侧边栏相关
    const sidebar = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebar-overlay');
    const closeSidebar = document.getElementById('close-sidebar');
    const menuBtn = document.getElementById('menu-btn'); // 新增历史记录按钮
    const historyList = document.getElementById('history-list');
    const newChatBtn = document.getElementById('new-chat-btn');
    const onlineIdeBtn = document.getElementById('online-ide-btn');

    // 历史会话数据
    let conversations = JSON.parse(localStorage.getItem('chatHistory') || '[]');
    let currentConversationId = null;

    // 打开/关闭侧边栏
    function openSidebar() {
        sidebar.classList.add('active');
        sidebarOverlay.classList.add('active');
        renderHistoryList(); // 每次打开时刷新历史记录
    }
    
    function closeSidebarFunc() {
        sidebar.classList.remove('active');
        sidebarOverlay.classList.remove('active');
    }
    
    // 添加侧边栏事件监听
    if (menuBtn) menuBtn.addEventListener('click', openSidebar); // 新增按钮事件
    if (closeSidebar) closeSidebar.addEventListener('click', closeSidebarFunc);
    if (sidebarOverlay) sidebarOverlay.addEventListener('click', closeSidebarFunc);

    // 渲染历史记录
    function renderHistoryList() {
        if (!historyList) return;
        
        historyList.innerHTML = '';
        if (conversations.length === 0) {
            historyList.innerHTML = '<div style="color:#aaa;text-align:center;padding:1.5em 0;">暂无历史对话</div>';
            return;
        }
        
        // 按时间倒序排列
        const sortedConversations = [...conversations].sort((a, b) => 
            new Date(b.createdAt || 0) - new Date(a.createdAt || 0)
        );
        
        sortedConversations.forEach(conv => {
            const item = document.createElement('div');
            item.className = 'history-item' + (conv.id === currentConversationId ? ' active' : '');
            
            // 格式化时间
            const createdTime = conv.createdAt ? new Date(conv.createdAt).toLocaleString() : '';
            
            item.innerHTML = `
                <div class="history-item-title">${conv.title || '未命名会话'}</div>
                <div class="history-item-preview">${conv.preview || ''}</div>
                <div class="history-item-time" style="font-size:0.7rem;color:#999;margin-top:0.2rem;">${createdTime}</div>
                <div class="history-item-actions" style="margin-top:0.3rem;">
                    <button class="delete-btn" onclick="deleteConversation('${conv.id}')" style="background:#3498db;color:white;border:none;padding:0.2rem 0.5rem;border-radius:3px;font-size:0.7rem;cursor:pointer;">删除</button>
                </div>
            `;
            item.onclick = (e) => {
                // 如果点击的是删除按钮，不加载对话
                if (e.target.classList.contains('delete-btn')) return;
                loadConversation(conv.id);
                closeSidebarFunc();
            };
            historyList.appendChild(item);
        });
    }

    // 删除对话
    window.deleteConversation = function(conversationId) {
        if (confirm('确定要删除这个对话吗？')) {
            conversations = conversations.filter(c => c.id !== conversationId);
            localStorage.setItem('chatHistory', JSON.stringify(conversations));
            
            // 如果删除的是当前对话，清空聊天界面
            if (currentConversationId === conversationId) {
                currentConversationId = null;
                messagesDiv.innerHTML = '';
            }
            
            renderHistoryList();
        }
    }

    // 加载会话
    function loadConversation(id) {
        const conv = conversations.find(c => c.id === id);
        if (!conv) return;
        
        currentConversationId = id;
        messagesDiv.innerHTML = '';
        
        // 加载对话历史
        if (conv.messages && conv.messages.length > 0) {
            conv.messages.forEach(msg => {
                appendMessage(msg.content, msg.sender, false);
            });
            // 滚动到底部
            setTimeout(() => {
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }, 100);
        }
        
        renderHistoryList(); // 更新active状态
    }

    // 保存消息到当前对话
    function saveMessageToHistory(content, sender) {
        if (!currentConversationId) {
            // 如果没有当前对话，创建新对话
            createNewConversation();
        }
        
        const currentConv = conversations.find(c => c.id === currentConversationId);
        if (currentConv) {
            if (!currentConv.messages) currentConv.messages = [];
            currentConv.messages.push({
                content: content,
                sender: sender,
                timestamp: new Date().toISOString()
            });
            
            // 更新对话标题和预览
            if (sender === 'user' && (!currentConv.title || currentConv.title === '新对话')) {
                currentConv.title = content.substring(0, 20) + (content.length > 20 ? '...' : '');
            }
            if (sender === 'ai') {
                currentConv.preview = content.substring(0, 50) + (content.length > 50 ? '...' : '');
                currentConv.lastUpdated = new Date().toISOString();
            }
            
            localStorage.setItem('chatHistory', JSON.stringify(conversations));
        }
    }

    // 创建新对话
    function createNewConversation() {
        const newConv = {
            id: Date.now().toString(),
            title: '新对话',
            preview: '',
            messages: [],
            createdAt: new Date().toISOString(),
            lastUpdated: new Date().toISOString()
        };
        conversations.unshift(newConv);
        currentConversationId = newConv.id;
        localStorage.setItem('chatHistory', JSON.stringify(conversations));
        messagesDiv.innerHTML = ''; // 清空当前对话
        renderHistoryList();
        return newConv;
    }

    // 新建对话按钮
    if (newChatBtn) {
        newChatBtn.addEventListener('click', function() {
            createNewConversation();
            closeSidebarFunc();
        });
    }

    // 在线IDE按钮
    if (onlineIdeBtn) {
        onlineIdeBtn.onclick = function() {
            window.open('https://www.techiedelight.com/compiler/zh/index', '_blank');
        };
    } else {
        // 兼容直接在HTML中定义的onclick
        window.click_event = function() {
            window.open('https://www.techiedelight.com/compiler/zh/index', '_blank');
        };
    }

    // 消息展示函数
    window.appendMessage = function(content, sender, isLoading = false) {
        const bubble = document.createElement('div');
        bubble.className = `bubble ${sender}` + (isLoading ? ' loading' : '');
        let displayContent = content;
        // 加载动画改为三个点
        if (isLoading && sender === 'ai') {
            displayContent = `<span class="loading-dot"><span>.</span><span>.</span><span>.</span></span>`;
        }
        bubble.innerHTML = `
            <div class="bubble-content">${displayContent}</div>
        `;
        messagesDiv.appendChild(bubble);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
        return bubble;
    }

    // 异步逐字输出
    window.typeWriter = async function(element, text, delay = 18) {
        element.innerHTML = '';
        for (let i = 0; i < text.length; i++) {
            element.innerHTML += text[i];
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
            await new Promise(res => setTimeout(res, delay));
        }
    }

    // 发送消息至服务器
    window.sendToOllamaStream = async function() {
        const question = input.value.trim();
        if (!question) return;

        input.value = '';
        input.disabled = true;
        sendBtn.disabled = true;

        appendMessage(question, 'user');
        saveMessageToHistory(question, 'user');

        // AI loading消息 - 显示加载动画
        const loadingBubble = appendMessage('', 'ai', true);
        const bubbleContent = loadingBubble.querySelector('.bubble-content');

        try {
            const resp = await fetch('https://api.siliconflow.cn/v1/chat/completions', {
                method: 'POST',
                headers: {
                    'Authorization': 'Bearer sk-xgrvmcsnotbrrypgtwtncaazflsfeeqaiuqkwwztabyhimnn',
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    model: "deepseek-ai/DeepSeek-R1",
                    messages: [{ role: "user", content: question }],
                    stream: true,
                    max_tokens: 512,
                    temperature: 0.7,
                    top_p: 0.7,
                    top_k: 50,
                    frequency_penalty: 0.5,
                })
            });

            if (!resp.ok) throw new Error(`HTTP错误 ${resp.status}`);

            const reader = resp.body.getReader();
            const decoder = new TextDecoder('utf-8');
            let buffer = '';
            let aiResponse = '';
            
            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });
                let lines = buffer.split('\n');
                buffer = lines.pop();
                for (let line of lines) {
                    line = line.trim();
                    if (!line || !line.startsWith('data:')) continue;
                    const dataStr = line.replace(/^data:\s*/, '');
                    if (dataStr === '[DONE]') break;
                    try {
                        const data = JSON.parse(dataStr);
                        const delta = data.choices?.[0]?.delta?.content || '';
                        if (delta) {
                            // 有内容输出时，关闭加载动画并开始显示内容
                            if (loadingBubble.classList.contains('loading')) {
                                loadingBubble.classList.remove('loading');
                                bubbleContent.innerHTML = ''; // 清空加载动画
                            }
                            aiResponse += delta;
                            bubbleContent.innerHTML += delta;
                            messagesDiv.scrollTop = messagesDiv.scrollHeight;
                        }
                    } catch (e) {}
                }
            }
            
            // 保存AI回复到历史记录
            if (aiResponse) {
                saveMessageToHistory(aiResponse, 'ai');
                renderHistoryList();
            }
        } catch (error) {
            loadingBubble.classList.remove('loading');
            bubbleContent.innerHTML = `<span style="color:#e74c3c;">❌ 请求失败: ${error.message}</span>`;
        } finally {
            input.disabled = false;
            sendBtn.disabled = false;
            input.focus();
        }
    }

    // 为Enter键绑定发送消息
    if (input) {
        input.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                window.sendToOllamaStream();
            }
        });
    }

    // 为发送按钮绑定发送消息
    if (sendBtn) {
        sendBtn.addEventListener('click', window.sendToOllamaStream);
    }

    // 页面初始化
    renderHistoryList();

    // 如果没有对话，创建默认对话
    if (conversations.length === 0) {
        createNewConversation();
    } else {
        // 如果有对话但没有当前对话，设置第一个为当前对话
        if (!currentConversationId && conversations.length > 0) {
            currentConversationId = conversations[0].id;
            loadConversation(currentConversationId);
        }
    }
});