// ==UserScript==
// @name         图片高亮查找工具
// @namespace    http://tampermonkey.net/
// @version      1.1
// @description  通过图片名快速查找并高亮网页中的图片
// @author       SocialClaw
// @match        *://*/*
// @grant        none
// @run-at       document-end
// ==/UserScript==

(function() {
    'use strict';

    // 全局变量
    let isPanelCreated = false;

    // 创建浮动搜索框
    function createSearchUI() {
        if (isPanelCreated) return;

        const style = document.createElement('style');
        style.textContent = `
            #image-highlighter-panel {
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 999999;
                background: rgba(255, 255, 255, 0.95);
                border: 2px solid #3498db;
                border-radius: 8px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
                padding: 15px;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
                display: none;
            }
            #image-highlighter-panel.active {
                display: block;
                animation: slideIn 0.3s ease;
            }
            @keyframes slideIn {
                from { transform: translateX(300px); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            .highlighter-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 10px;
                padding-bottom: 10px;
                border-bottom: 1px solid #eee;
            }
            .highlighter-title {
                font-weight: bold;
                color: #2c3e50;
                font-size: 16px;
            }
            .highlighter-close {
                background: #e74c3c;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                cursor: pointer;
                font-size: 14px;
            }
            .highlighter-close:hover {
                background: #c0392b;
            }
            .highlighter-input-group {
                margin-bottom: 10px;
            }
            .highlighter-input-group label {
                display: block;
                margin-bottom: 5px;
                color: #34495e;
                font-size: 13px;
            }
            .highlighter-input {
                width: 100%;
                padding: 8px 12px;
                border: 2px solid #bdc3c7;
                border-radius: 4px;
                font-size: 14px;
                outline: none;
                transition: border-color 0.3s;
            }
            .highlighter-input:focus {
                border-color: #3498db;
            }
            .highlighter-input.valid {
                border-color: #27ae60;
            }
            .highlighter-input.invalid {
                border-color: #e74c3c;
            }
            .highlighter-buttons {
                display: flex;
                gap: 8px;
                margin-top: 10px;
            }
            .highlighter-btn {
                flex: 1;
                padding: 8px 12px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 500;
                transition: all 0.2s;
            }
            .highlighter-btn-primary {
                background: #3498db;
                color: white;
            }
            .highlighter-btn-primary:hover {
                background: #2980b9;
            }
            .highlighter-btn-secondary {
                background: #95a5a6;
                color: white;
            }
            .highlighter-btn-secondary:hover {
                background: #7f8c8d;
            }
            .highlighter-status {
                margin-top: 8px;
                padding: 8px;
                border-radius: 4px;
                font-size: 12px;
                display: none;
            }
            .highlighter-status.success {
                background: #d5f5e3;
                color: #27ae60;
                display: block;
            }
            .highlighter-status.error {
                background: #fadbd8;
                color: #c0392b;
                display: block;
            }
            .highlighter-status.info {
                background: #ebf5fb;
                color: #2980b9;
                display: block;
            }
            .highlighter-results {
                margin-top: 10px;
                max-height: 200px;
                overflow-y: auto;
                border-top: 1px solid #eee;
                padding-top: 10px;
            }
            .highlighter-result-item {
                padding: 8px;
                margin-bottom: 5px;
                background: #f8f9fa;
                border-radius: 4px;
                cursor: pointer;
                transition: background 0.2s;
            }
            .highlighter-result-item:hover {
                background: #e9ecef;
            }
            .highlighter-result-item.highlighted {
                background: #d5f5e3;
                border-left: 3px solid #27ae60;
            }
            .highlighter-result-info {
                font-size: 12px;
                color: #7f8c8d;
                margin-top: 3px;
            }
        `;
        document.head.appendChild(style);

        const panel = document.createElement('div');
        panel.id = 'image-highlighter-panel';
        panel.innerHTML = `
            <div class="highlighter-header">
                <div class="highlighter-title">🖼️ 图片查找工具</div>
                <button class="highlighter-close" id="highlighter-close">×</button>
            </div>
            <div class="highlighter-input-group">
                <label for="highlighter-search">输入图片名 (支持模糊搜索)</label>
                <input type="text" id="highlighter-search" class="highlighter-input" placeholder="例如: avatar.jpg 或 avatar" autocomplete="off">
            </div>
            <div class="highlighter-buttons">
                <button class="highlighter-btn highlighter-btn-primary" id="highlighter-search-btn">🔍 搜索</button>
                <button class="highlighter-btn highlighter-btn-secondary" id="highlighter-clear-btn">✗ 清除</button>
            </div>
            <div id="highlighter-status" class="highlighter-status"></div>
            <div id="highlighter-results" class="highlighter-results"></div>
        `;
        document.body.appendChild(panel);
        isPanelCreated = true;

        // 绑定事件
        document.getElementById('highlighter-close').addEventListener('click', togglePanel);
        document.getElementById('highlighter-search-btn').addEventListener('click', searchImages);
        document.getElementById('highlighter-clear-btn').addEventListener('click', clearHighlights);

        const searchInput = document.getElementById('highlighter-search');
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                searchImages();
            }
        });
        searchInput.addEventListener('input', (e) => {
            validateInput(e.target);
        });

        return panel;
    }

    // 切换面板显示
    function togglePanel() {
        const panel = document.getElementById('image-highlighter-panel');
        if (!panel) return;
        panel.classList.toggle('active');
        if (panel.classList.contains('active')) {
            document.getElementById('highlighter-search').focus();
        } else {
            clearHighlights();
        }
    }

    // 验证输入
    function validateInput(input) {
        const value = input.value.trim();
        if (value.length >= 2) {
            input.classList.add('valid');
            input.classList.remove('invalid');
            return true;
        } else {
            input.classList.remove('valid');
            input.classList.add('invalid');
            return false;
        }
    }

    // 搜索图片
    function searchImages() {
        const input = document.getElementById('highlighter-search');
        const searchTerm = input.value.trim();

        if (!validateInput(input)) {
            showStatus(`请输入至少2个字符`, 'error');
            return;
        }

        clearHighlights();

        const images = document.querySelectorAll('img');
        const results = [];
        const matchedImages = [];

        // 匹配逻辑
        images.forEach((img, index) => {
            const src = img.src || '';
            const alt = img.alt || '';
            const filename = src.split('/').pop().split('?')[0].split('#')[0];

            // 匹配文件名（不区分大小写）
            const regex = new RegExp(searchTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'i');

            if (regex.test(filename) || regex.test(alt)) {
                results.push({
                    index: index + 1,
                    img: img,
                    filename: filename,
                    alt: alt,
                    src: src
                });
                matchedImages.push(img);
            }
        });

        // 显示结果
        if (results.length > 0) {
            showStatus(`找到 ${results.length} 个匹配的图片`, 'success');
            displayResults(results);
            highlightImages(matchedImages);

            // 自动滚动到第一个结果
            if (matchedImages.length > 0) {
                setTimeout(() => {
                    matchedImages[0].scrollIntoView({ behavior: 'smooth', block: 'center' });
                }, 300);
            }
        } else {
            showStatus(`未找到匹配 "${searchTerm}" 的图片`, 'error');
        }
    }

    // 显示搜索结果列表
    function displayResults(results) {
        const resultsContainer = document.getElementById('highlighter-results');
        resultsContainer.innerHTML = '';

        results.forEach((result, i) => {
            const item = document.createElement('div');
            item.className = 'highlighter-result-item';
            item.innerHTML = `
                <strong>图片 #${result.index}</strong>
                <div class="highlighter-result-info">
                    文件名: ${result.filename || '无'}
                    ${result.alt ? `<br>Alt: ${result.alt}` : ''}
                </div>
            `;
            item.addEventListener('click', () => {
                result.img.scrollIntoView({ behavior: 'smooth', block: 'center' });
                setTimeout(() => {
                    result.img.classList.add('highlighted');
                }, 100);
            });
            resultsContainer.appendChild(item);
        });
    }

    // 高亮图片
    function highlightImages(images) {
        images.forEach((img, index) => {
            // 添加高亮样式
            img.style.outline = '3px solid #f1c40f';
            img.style.outlineOffset = '2px';
            img.style.boxShadow = '0 0 20px rgba(241, 196, 15, 0.5)';
            img.style.transition = 'all 0.3s ease';

            // 添加高亮标记
            const highlightDiv = document.createElement('div');
            highlightDiv.className = 'image-highlight-marker';
            highlightDiv.style.cssText = `
                position: absolute;
                top: 5px;
                right: 5px;
                background: #f1c40f;
                color: #2c3e50;
                border-radius: 50%;
                width: 24px;
                height: 24px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: bold;
                font-size: 12px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                z-index: 10000;
                pointer-events: none;
            `;
            highlightDiv.textContent = index + 1;

            // 如果图片在容器内，将标记添加到容器
            const parent = img.parentElement;
            if (parent && getComputedStyle(parent).position !== 'static') {
                parent.style.position = 'relative';
                parent.appendChild(highlightDiv);
            } else {
                // 否则创建一个包裹容器
                const wrapper = document.createElement('div');
                wrapper.style.cssText = 'display: inline-block; position: relative;';
                img.parentNode.insertBefore(wrapper, img);
                wrapper.appendChild(img);
                wrapper.appendChild(highlightDiv);
            }

            img.dataset.highlighted = 'true';
        });
    }

    // 清除高亮
    function clearHighlights() {
        // 移除高亮样式
        document.querySelectorAll('img[data-highlighted="true"]').forEach(img => {
            img.style.outline = '';
            img.style.outlineOffset = '';
            img.style.boxShadow = '';
            img.style.transition = '';
            img.removeAttribute('data-highlighted');
        });

        // 移除高亮标记
        document.querySelectorAll('.image-highlight-marker').forEach(marker => {
            marker.remove();
        });

        // 移除包裹容器（如果存在）
        document.querySelectorAll('div[style*="display: inline-block; position: relative;"]').forEach(wrapper => {
            if (wrapper.children.length === 1 && wrapper.firstChild.tagName === 'IMG') {
                const img = wrapper.firstChild;
                wrapper.parentNode.insertBefore(img, wrapper);
                wrapper.remove();
            }
        });

        // 清空结果列表
        document.getElementById('highlighter-results').innerHTML = '';

        // 清空输入框
        document.getElementById('highlighter-search').value = '';
        document.getElementById('highlighter-search').classList.remove('valid', 'invalid');

        showStatus('');
    }

    // 显示状态消息
    function showStatus(message, type = '') {
        const statusDiv = document.getElementById('highlighter-status');
        statusDiv.textContent = message;
        statusDiv.className = 'highlighter-status';
        if (type) {
            statusDiv.classList.add(type);
        }
    }

    // 右键菜单集成
    document.addEventListener('contextmenu', (e) => {
        if (e.target.tagName === 'IMG') {
            const img = e.target;
            const filename = img.src.split('/').pop().split('?')[0];

            // 创建临时菜单项
            setTimeout(() => {
                createSearchUI();
                const panel = document.getElementById('image-highlighter-panel');
                if (!panel) return;

                const input = document.getElementById('highlighter-search');
                input.value = filename;
                validateInput(input);
                togglePanel();
            }, 100);
        }
    });

    // 全局快捷键监听
    document.addEventListener('keydown', (e) => {
        // Ctrl + Shift + F 打开搜索框
        if (e.ctrlKey && e.shiftKey && e.key === 'F') {
            e.preventDefault();
            createSearchUI();
            togglePanel();
        }
        // ESC 关闭搜索框
        const panel = document.getElementById('image-highlighter-panel');
        if (e.key === 'Escape' && panel && panel.classList.contains('active')) {
            e.preventDefault();
            togglePanel();
        }
    });

    // 初始化
    createSearchUI();

    // 添加右键菜单提示
    console.log('%c🖼️ 图片高亮查找工具已加载', 'color: #3498db; font-weight: bold;');
    console.log('%c使用方法:', 'color: #27ae60; font-weight: bold;');
    console.log('%c1. Ctrl + Shift + F - 打开搜索面板', 'color: #34495e;');
    console.log('%c2. 输入图片名（支持模糊搜索）', 'color: #34495e;');
    console.log('%c3. 点击搜索或按 Enter', 'color: #34495e;');
    console.log('%c4. 右键点击图片 - 快速搜索该图片', 'color: #34495e;');
    console.log('%c5. ESC - 关闭面板', 'color: #34495e;');

})();
