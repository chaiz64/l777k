// ==UserScript==
// @name         NotebookLM to Markdown Export (V3 - Native Format)
// @namespace    http://tampermonkey.net/
// @version      3.0
// @description  Exports NotebookLM chat with proper Markdown formatting (Bold, Lists, Headers).
// @match        https://notebooklm.google.com/*
// @grant        none
// ==/UserScript==

(function() {
    'use strict';

    // Minimal HTML to Markdown converter
    function parseNodeToMarkdown(node) {
        if (node.nodeType === Node.TEXT_NODE) {
            return node.textContent;
        }

        if (node.nodeType !== Node.ELEMENT_NODE) {
            return "";
        }

        let tag = node.tagName.toLowerCase();
        
        if (tag === 'br') return '\n';
        if (tag === 'hr') return '\n---\n\n';

        let childrenMarkdown = "";
        for (let child of node.childNodes) {
            childrenMarkdown += parseNodeToMarkdown(child);
        }

        switch (tag) {
            case 'p':
            case 'div':
            case 'article':
            case 'section':
                return '\n\n' + childrenMarkdown + '\n\n';
            case 'h1': return '\n\n# ' + childrenMarkdown + '\n\n';
            case 'h2': return '\n\n## ' + childrenMarkdown + '\n\n';
            case 'h3': return '\n\n### ' + childrenMarkdown + '\n\n';
            case 'h4': return '\n\n#### ' + childrenMarkdown + '\n\n';
            case 'h5': return '\n\n##### ' + childrenMarkdown + '\n\n';
            case 'h6': return '\n\n###### ' + childrenMarkdown + '\n\n';
            case 'strong':
            case 'b':
                return '**' + childrenMarkdown + '**';
            case 'em':
            case 'i':
                return '*' + childrenMarkdown + '*';
            case 'code':
                if (node.parentNode && node.parentNode.tagName.toLowerCase() === 'pre') {
                    return childrenMarkdown; 
                }
                return '`' + childrenMarkdown + '`';
            case 'pre':
                return '\n\n```\n' + childrenMarkdown + '\n```\n\n';
            case 'blockquote':
                return '\n\n> ' + childrenMarkdown.replace(/\n/g, '\n> ') + '\n\n';
            case 'ul':
            case 'ol':
                return '\n' + childrenMarkdown + '\n';
            case 'li':
                let prefix = node.parentNode && node.parentNode.tagName.toLowerCase() === 'ol' ? '1. ' : '- ';
                return '\n' + prefix + childrenMarkdown.trim();
            case 'a':
                return '[' + childrenMarkdown + '](' + node.getAttribute('href') + ')';
            case 'span':
                return childrenMarkdown;
            default:
                return childrenMarkdown;
        }
    }

    function cleanMarkdown(md) {
        md = md.replace(/\n{3,}/g, '\n\n'); // Remove extra blank lines
        md = md.replace(/\*\* \*\*/g, '');  // Clean empty bolds
        md = md.replace(/\* \*/g, '');      // Clean empty italics
        return md.trim();
    }

    function exportToMarkdown() {
        // Find main chat container
        let chatContainer = document.querySelector('div[role="log"]') || 
                            document.querySelector('main') || 
                            document.body;

        // Clone so we don't mess up the actual UI
        let clone = chatContainer.cloneNode(true);

        // Strip out buttons, icons, and menus before parsing
        let junkSelectors = [
            'button', 
            'textarea', 
            'nav', 
            'header', 
            'svg', 
            '[role="toolbar"]',
            '[aria-label*="emoji"]',
            '[aria-label*="Recently used"]',
            '.clip-board-button'
        ];
        
        junkSelectors.forEach(sel => {
            clone.querySelectorAll(sel).forEach(el => el.remove());
        });

        // Convert the clean HTML into Markdown syntax
        let rawMarkdown = parseNodeToMarkdown(clone);
        let finalMarkdown = cleanMarkdown(rawMarkdown);

        if (!finalMarkdown) {
            alert("No content found. Please make sure the chat is fully loaded.");
            return;
        }

        // Generate file
        let blob = new Blob([finalMarkdown], { type: 'text/markdown' });
        let url = window.URL.createObjectURL(blob);
        let a = document.createElement('a');
        
        let dateStr = new Date().toISOString().slice(0,10);
        a.href = url;
        a.download = 'NotebookLM_Chat_' + dateStr + '.md';
        a.style.display = 'none';
        
        document.body.appendChild(a);
        a.click();
        
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    }

    function createExportButton() {
        if (document.getElementById('nblm-export-btn')) return;

        let btn = document.createElement('button');
        btn.id = 'nblm-export-btn';
        btn.innerText = 'Export MD (Formatted)';
        
        btn.style.position = 'fixed';
        btn.style.bottom = '24px';
        btn.style.right = '24px';
        btn.style.zIndex = '999999';
        btn.style.padding = '12px 20px';
        btn.style.backgroundColor = '#10b981'; 
        btn.style.color = '#ffffff';
        btn.style.border = 'none';
        btn.style.borderRadius = '8px';
        btn.style.fontSize = '14px';
        btn.style.fontWeight = 'bold';
        btn.style.cursor = 'pointer';
        btn.style.boxShadow = '0 4px 6px rgba(0,0,0,0.1)';
        btn.style.transition = 'background-color 0.2s';

        btn.onmouseover = function() {
            btn.style.backgroundColor = '#059669';
        };
        btn.onmouseout = function() {
            btn.style.backgroundColor = '#10b981';
        };

        btn.onclick = exportToMarkdown;

        document.body.appendChild(btn);
    }

    let observer = new MutationObserver(function() {
        if (!document.getElementById('nblm-export-btn')) {
            createExportButton();
        }
    });

    observer.observe(document.body, { childList: true, subtree: true });
    createExportButton();

})();
