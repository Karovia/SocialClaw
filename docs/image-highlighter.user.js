// ==UserScript==
// @name         图片高亮显示工具
// @namespace    http://tampermonkey.net/
// @version      1.0
// @description  根据文件名查找并高亮显示图片，支持滚动定位和链接高亮
// @author       SocialClaw
// @match        *://*/*
// @grant        GM_registerMenuCommand
// @grant        GM_getValue
// @grant        GM_setValue
// @run-at       document-end
// ==/UserScript==

(function() {
    'use strict';

    // 默认目标图片文件名
    const DEFAULT_TARGET_FILENAME = "049068bb58bdb600879cf1fddce90887.png";

    // 配置选项
    const CONFIG = {
        highlightBorder: "3px solid red",          // 图片高亮边框样式
        linkBorder: "2px solid blue",              // 链接高亮边框样式
        scrollBehavior: "smooth",                  // 滚动行为: smooth 或 auto
        scrollBlock: "center",                     // 滚动对齐: start, center, end, nearest
        highlightDuration: 3000,                   // 高亮持续时间(毫秒)，0为永久
        autoExecute: false                         // 页面加载后是否自动执行
    };

    /**
     * 查找并高亮指定文件名的图片
     * @param {string} targetFilename - 目标图片文件名
     */
    function highlightImage(targetFilename) {
        console.log(`🔍 开始查找图片: ${targetFilename}`);

        // 通过 src 属性包含文件名进行搜索
        const targetImage = document.querySelector(`img[src*="${targetFilename}"]`);

        if (!targetImage) {
            console.log(`❌ 未找到文件名为 "${targetFilename}" 的图片`);
            alert(`未找到文件名为 "${targetFilename}" 的图片`);
            return;
        }

        console.log("✅ 找到对应的图片元素：", targetImage);

        // 高亮显示图片
        const originalBorder = targetImage.style.border;
        targetImage.style.border = CONFIG.highlightBorder;
        targetImage.style.boxShadow = "0 0 10px rgba(255, 0, 0, 0.5)";

        // 滚动到图片位置
        targetImage.scrollIntoView({
            behavior: CONFIG.scrollBehavior,
            block: CONFIG.scrollBlock
        });

        // 查找父级标签或链接
        const parentLink = targetImage.closest('a');
        let originalLinkBorder = '';
        if (parentLink) {
            console.log("🔗 图片所在的链接：", parentLink.href);
            originalLinkBorder = parentLink.style.border;
            parentLink.style.border = CONFIG.linkBorder;
            parentLink.style.display = 'inline-block';
            parentLink.style.padding = '2px';
        }

        // 打印周围 HTML
        console.log("📄 周围 HTML 片段：", targetImage.outerHTML);

        // 显示找到的信息
        const info = `找到图片: ${targetFilename}\n` +
                     `图片地址: ${targetImage.src}\n` +
                     `尺寸: ${targetImage.naturalWidth}x${targetImage.naturalHeight}\n` +
                     (parentLink ? `链接地址: ${parentLink.href}\n` : '');
        console.log(info);

        // 如果设置了高亮持续时间，到时后恢复原状
        if (CONFIG.highlightDuration > 0) {
            setTimeout(() => {
                targetImage.style.border = originalBorder;
                targetImage.style.boxShadow = '';
                if (parentLink) {
                    parentLink.style.border = originalLinkBorder;
                }
                console.log("🕐 高亮效果已移除");
            }, CONFIG.highlightDuration);
        }
    }

    /**
     * 显示输入对话框，获取要查找的图片文件名
     */
    function promptForFilename() {
        const lastFilename = GM_getValue('lastFilename', DEFAULT_TARGET_FILENAME);
        const filename = prompt('请输入要查找的图片文件名:', lastFilename);

        if (filename && filename.trim() !== '') {
            const cleanFilename = filename.trim();
            GM_setValue('lastFilename', cleanFilename);
            highlightImage(cleanFilename);
        } else if (filename !== null) {
            alert('请输入有效的文件名！');
        }
    }

    /**
     * 初始化脚本
     */
    function init() {
        // 注册油猴菜单命令
        GM_registerMenuCommand('🔍 高亮显示图片', promptForFilename);

        // 如果设置了自动执行，则使用默认文件名
        if (CONFIG.autoExecute) {
            highlightImage(DEFAULT_TARGET_FILENAME);
        }

        console.log('✅ 图片高亮显示工具已加载');
        console.log('💡 使用方法: 点击油猴图标 -> 选择 "🔍 高亮显示图片"');
    }

    // 页面加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
