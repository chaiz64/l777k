// ==UserScript==
// @name         NotebookLM to Markdown Export (V7 - Final Polish)
// @namespace    http://tampermonkey.net/
// @version      7.0
// @description  Fixes squashed lines (YAML/Divs) and removes injected empty frontmatter.
// @match        https://notebooklm.google.com/*
// @grant        none
// ==/UserScript==

(function() {
    'use strict';

    function parseNodeToMarkdown(node) {
        if (node.nodeType === Node.TEXT_NODE) {
            return node.textContent;
        }
        if (node.nodeType !== Node.ELEMENT_NODE) {
            return "";
        }

        let tag = node.tagName.toLowerCase();
        let childrenMarkdown = "";

        for (let child of node.childNodes) {
            childrenMarkdown += parseNodeToMarkdown(child);
        }

        switch (tag) {
            case 'br': return '\n';
            case 'hr': return '\n---\n\n';
            case 'p': return '\n\n' + childrenMarkdown + '\n\n';
            case 'div':
            case 'section':
            case 'article':
            case 'main':
                return '\n' + childrenMarkdown + '\n';
            case 'li':
                let prefix = node.parentNode && node.parentNode.tagName.toLowerCase() === 'ol' ? '1. ' : '- ';
                return '\n' + prefix + childrenMarkdown.trim();
            case 'h1': return '\n\n# ' + childrenMarkdown + '\n\n';
            case 'h2': return '\n\n## ' + childrenMarkdown + '\n\n';
            case 'h3': return '\n\n### ' + childrenMarkdown + '\n\n';
            case 'h4': return '\n\n#### ' + childrenMarkdown + '\n\n';
            case 'strong':
            case 'b': return '**' + childrenMarkdown.trim() + '** ';
            case 'em':
            case 'i': return '*' + childrenMarkdown.trim() + '* ';
            case 'code':
                if (node.parentNode && node.parentNode.tagName.toLowerCase() === 'pre') return childrenMarkdown;
                return '`' + childrenMarkdown + '`';
            case 'pre':
                // Auto-remove prompt configuration blocks
                if (childrenMarkdown.includes('task:') && childrenMarkdown.includes('role:')) {
                    return '';
                }
                return '\n\n```\n' + childrenMarkdown.trim() + '\n```\n\n';
            case 'blockquote': return '\n\n> ' + childrenMarkdown.trim().replace(/\n/g, '\n> ') + '\n\n';
            case 'ul':
            case 'ol': return '\n' + childrenMarkdown + '\n';
            case 'a': return '[' + childrenMarkdown + '](' + node.getAttribute('href') + ')';
            case 'span':
                return childrenMarkdown;
            default:
                return childrenMarkdown;
        }
    }

    function exportToMarkdown() {
        let bestContainer = null;
        let maxScore = -1;

        let candidateContainers = document.querySelectorAll('div, main, section');
        candidateContainers.forEach(container => {
            let pCount = container.querySelectorAll('p').length;
            let textLen = container.innerText ? container.innerText.trim().length : 0;

            if (container.tagName === 'BODY' || container.tagName === 'HTML') return;

            let score = pCount * 100 + textLen;
            if (textLen > document.body.innerText.length * 0.9) score = score / 2;

            if (score > maxScore && pCount > 0) {
                maxScore = score;
                bestContainer = container;
            }
        });

        if (!bestContainer) bestContainer = document.querySelector('main') || document.body;

        let clone = bestContainer.cloneNode(true);

        let junkSelectors = [
            'button', 'textarea', 'input', 'nav', 'header', 'svg', 'img',
            '[role="button"]', '[role="toolbar"]', '[role="navigation"]', '[role="menu"]',
            '[aria-label*="emoji"]', '[aria-label*="Recently used"]',
            '.cdk-overlay-container', '[class*="tooltip"]', '[class*="icon"]'
        ];

        junkSelectors.forEach(selector => {
            clone.querySelectorAll(selector).forEach(el => el.remove());
        });

        let rawMarkdown = parseNodeToMarkdown(clone);

        let lines = rawMarkdown.split('\n');
        let cleanLines = lines.filter(line => {
            let t = line.trim();
            if (t === '') return true;

            let junkList = [
                'Search results', 'No emoji found', 'Recently used',
                'Loading', 'Start typing...', 'Save to note',
                'Chat', 'Studio', 'Sources', 'PLUS', '👁️',
                'SourcesChatStudio', 'SourcesChat', 'ChatStudio'
            ];

            if (junkList.includes(t)) return false;
            if (/^[0-9]+\s+source(s)?$/.test(t)) return false;
            
            // Filter timestamps like "Today • 12:19 PM"
            if (/^(Today|Yesterday|[A-Za-z]+)\s•\s[0-9]{1,2}:[0-9]{2}\s(AM|PM)/i.test(t)) return false;

            return true;
        });

        let finalMarkdown = cleanLines.join('\n');
        finalMarkdown = finalMarkdown.replace(/\n{3,}/g, '\n\n').trim();

        if (!finalMarkdown || finalMarkdown === "") {
            alert("Export failed: Could not extract text. Please scroll through the chat to load content and try again.");
            return;
        }

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
        if (document.getElementById('nblm-export-btn-v7')) return;

        let btn = document.createElement('button');
        btn.id = 'nblm-export-btn-v7';
        btn.innerText = 'Export MD (V7)';

        btn.style.position = 'fixed';
        btn.style.bottom = '80px';
        btn.style.right = '24px';
        btn.style.zIndex = '999999';
        btn.style.padding = '12px 20px';
        btn.style.backgroundColor = '#0ea5e9'; 
        btn.style.color = '#ffffff';
        btn.style.border = 'none';
        btn.style.borderRadius = '8px';
        btn.style.fontSize = '14px';
        btn.style.fontWeight = 'bold';
        btn.style.cursor = 'pointer';
        btn.style.boxShadow = '0 4px 6px rgba(0,0,0,0.3)';

        btn.onclick = exportToMarkdown;
        document.body.appendChild(btn);
    }

    let observer = new MutationObserver(function() {
        if (!document.getElementById('nblm-export-btn-v7')) {
            createExportButton();
        }
    });

    observer.observe(document.body, { childList: true, subtree: true });
    createExportButton();

})();
