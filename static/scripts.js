document.addEventListener('DOMContentLoaded', function() {
    // 侧边栏相关
    const sidebar = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebar-overlay');
    const closeSidebar = document.getElementById('close-sidebar');
    const showHistoryBtn = document.getElementById('show-history-btn');
    const refreshHistoryBtn = document.getElementById('refresh-history-btn');
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
    }
    function closeSidebarFunc() {
        sidebar.classList.remove('active');
        sidebarOverlay.classList.remove('active');
    }
    showHistoryBtn.addEventListener('click', openSidebar);
    closeSidebar.addEventListener('click', closeSidebarFunc);
    sidebarOverlay.addEventListener('click', closeSidebarFunc);

    // 渲染历史记录
    function renderHistoryList() {
        historyList.innerHTML = '';
        if (conversations.length === 0) {
            historyList.innerHTML = '<div style="color:#aaa;text-align:center;padding:1.5em 0;">暂无历史对话</div>';
            return;
        }
        conversations.forEach(conv => {
            const item = document.createElement('div');
            item.className = 'history-item' + (conv.id === currentConversationId ? ' active' : '');
            item.innerHTML = `
                <div class="history-item-title">${conv.title || '未命名会话'}</div>
                <div class="history-item-preview">${conv.preview || ''}</div>
            `;
            item.onclick = () => {
                loadConversation(conv.id);
                closeSidebarFunc();
            };
            historyList.appendChild(item);
        });
    }

    // 刷新历史记录
    refreshHistoryBtn.addEventListener('click', function() {
        conversations = JSON.parse(localStorage.getItem('chatHistory') || '[]');
        renderHistoryList();
    });

    // 新建对话
    newChatBtn.addEventListener('click', function() {
        const newConv = {
            id: Date.now().toString(),
            title: '新对话',
            preview: '',
            messages: []
        };
        conversations.unshift(newConv);
        currentConversationId = newConv.id;
        localStorage.setItem('chatHistory', JSON.stringify(conversations));
        renderHistoryList();
        closeSidebarFunc();
    });

    // 加载会话
    function loadConversation(id) {
        const conv = conversations.find(c => c.id === id);
        if (!conv) return;
        currentConversationId = id;
        // 渲染消息到聊天窗口
        // ...你可以根据你的消息渲染逻辑补充...
    }

    // 在线IDE按钮
    if (onlineIdeBtn) {
        onlineIdeBtn.onclick = function() {
            window.open('https://tools.qzxdp.cn/runcode', '_blank');
        };
    }

    // 页面初始化
    renderHistoryList();

    // ...existing code...
});