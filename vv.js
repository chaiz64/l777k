// ==UserScript==
// @name         NotebookLM to Markdown Export (V5)
// @namespace    http://tampermonkey.net/
// @version      5.0
// @description  Extracts formatted chat text specifically optimized for mobile views.
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
            case 'pre': return '\n\n```\n' + childrenMarkdown + '\n```\n\n';
            case 'blockquote': return '\n\n> ' + childrenMarkdown.replace(/\n/g, '\n> ') + '\n\n';
            case 'ul':
            case 'ol': return '\n' + childrenMarkdown + '\n';
            case 'li':
                let prefix = node.parentNode && node.parentNode.tagName.toLowerCase() === 'ol' ? '1. ' : '- ';
                return '\n' + prefix + childrenMarkdown.trim();
            case 'a': return '[' + childrenMarkdown + '](' + node.getAttribute('href') + ')';
            case 'div':
            case 'span':
            case 'section':
            case 'article':
            case 'main':
                return childrenMarkdown;
            default:
                return childrenMarkdown;
        }
    }

    function exportToMarkdown() {
        // 1. Locate the chat container using the scoring system (From V2)
        let bestContainer = null;
        let maxScore = -1;

        let candidateContainers = document.querySelectorAll('div, main, section');
        candidateContainers.forEach(container => {
            let paragraphCount = container.querySelectorAll('p').length;
            let textLength = container.innerText ? container.innerText.trim().length : 0;
            
            if (container.tagName === 'BODY' || container.tagName === 'HTML') return;
            
            let score = paragraphCount * 100 + textLength;
            
            if (textLength > document.body.innerText.length * 0.9) {
                score = score / 2;
            }

            if (score > maxScore && paragraphCount > 0) {
                maxScore = score;
                bestContainer = container;
            }
        });

        if (!bestContainer) {
            bestContainer = document.querySelector('main') || document.body;
        }

        // 2. Clone the container to manipulate it safely without breaking UI
        let clone = bestContainer.cloneNode(true);

        // 3. Purge unwanted UI elements
        let junkSelectors = [
            'button', 
            'textarea', 
            'input', 
            'nav', 
            'header', 
            'svg', 
            'img',
            '[role="button"]', 
            '[role="toolbar"]', 
            '[role="navigation"]',
            '[role="menu"]',
            '[aria-label*="emoji"]', 
            '[aria-label*="Recently used"]',
            '.cdk-overlay-container',
            '[class*="tooltip"]',
            '[class*="icon"]'
        ];

        junkSelectors.forEach(selector => {
            clone.querySelectorAll(selector).forEach(el => el.remove());
        });

        // 4. Convert to Markdown (From V3)
        let rawMarkdown = parseNodeToMarkdown(clone);

        // 5. Clean up the resulting text
        let lines = rawMarkdown.split('\n');
        let cleanLines = lines.filter(line => {
            let t = line.trim();
            if (t === '') return true;
            
            let junkList = [
                'Search results', 'No emoji found', 'Recently used', 
                'Loading', 'Start typing...', 'Save to note',
                'Chat', 'Studio', 'Sources', 'PLUS'
            ];
            
            if (junkList.includes(t)) return false;
            if (/^[0-9]+\s+source(s)?$/.test(t)) return false;
            
            return true;
        });

        let finalMarkdown = cleanLines.join('\n');
        finalMarkdown = finalMarkdown.replace(/\n{3,}/g, '\n\n').trim();

        if (!finalMarkdown || finalMarkdown === "") {
            alert("Export failed: Could not extract text. Please scroll through the chat to load content and try again.");
            return;
        }

        // 6. Trigger Download
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
        if (document.getElementById('nblm-export-btn-v5')) return;

        let btn = document.createElement('button');
        btn.id = 'nblm-export-btn-v5';
        btn.innerText = 'Export MD (V5)';
        
        btn.style.position = 'fixed';
        btn.style.bottom = '80px'; 
        btn.style.right = '24px';
        btn.style.zIndex = '999999';
        btn.style.padding = '12px 20px';
        btn.style.backgroundColor = '#f59e0b'; // Amber Color
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
        if (!document.getElementById('nblm-export-btn-v5')) {
            createExportButton();
        }
    });

    observer.observe(document.body, { childList: true, subtree: true });
    createExportButton();

})();
