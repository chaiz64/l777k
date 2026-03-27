// ==UserScript==
// @name         NotebookLM to Markdown Export (V8 - True Clipboard)
// @namespace    http://tampermonkey.net/
// @version      8.0
// @description  Perfectly replicates clipboard copy-paste formatting using Turndown.js.
// @match        https://notebooklm.google.com/*
// @require      https://unpkg.com/turndown/dist/turndown.js
// @grant        none
// ==/UserScript==

(function() {
    'use strict';

    function cleanMarkdown(md) {
        let lines = md.split('\n');
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
            
            // Filter timestamps 
            if (/^(Today|Yesterday|[A-Za-z]+)\s•\s[0-9]{1,2}:[0-9]{2}\s(AM|PM)/i.test(t)) return false;
            
            return true;
        });

        let finalMarkdown = cleanLines.join('\n');
        
        // Remove excessive newlines but maintain standard paragraph spacing
        finalMarkdown = finalMarkdown.replace(/\n{3,}/g, '\n\n').trim();
        return finalMarkdown;
    }

    function exportToMarkdown() {
        // Verify Turndown.js is loaded via @require
        if (typeof TurndownService === 'undefined') {
            alert("Turndown library failed to load. Please ensure Tampermonkey allows @require scripts.");
            return;
        }

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

        // Initialize standard HTML to Markdown converter
        let turndownService = new TurndownService({
            headingStyle: 'atx',
            codeBlockStyle: 'fenced',
            bulletListMarker: '-',
            strongDelimiter: '**',
            emDelimiter: '*'
        });
        
        // Prevent Turndown from aggressively escaping characters like clipboard does
        turndownService.escape = function (string) {
            return string; 
        };

        let rawMarkdown = turndownService.turndown(clone.innerHTML);
        let finalMarkdown = cleanMarkdown(rawMarkdown);

        if (!finalMarkdown || finalMarkdown === "") {
            alert("Export failed: Could not extract text. Please scroll through the chat to load content.");
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
        if (document.getElementById('nblm-export-btn-v8')) return;

        let btn = document.createElement('button');
        btn.id = 'nblm-export-btn-v8';
        btn.innerText = 'Export MD (Clipboard Format)';
        
        btn.style.position = 'fixed';
        btn.style.bottom = '80px'; 
        btn.style.right = '24px';
        btn.style.zIndex = '999999';
        btn.style.padding = '12px 20px';
        btn.style.backgroundColor = '#14b8a6'; 
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
        if (!document.getElementById('nblm-export-btn-v8')) {
            createExportButton();
        }
    });

    observer.observe(document.body, { childList: true, subtree: true });
    createExportButton();

})();
