// ==UserScript==
// @name         NotebookLM to Markdown Export (V2)
// @namespace    http://tampermonkey.net/
// @version      2.0
// @description  Injects a floating button to export NotebookLM chat content to a Markdown file.
// @match        https://notebooklm.google.com/*
// @grant        none
// ==/UserScript==

(function() {
    'use strict';

    function exportToMarkdown() {
        // 1. Find the best container for the chat using a scoring system
        let targetArea = null;
        let maxScore = 0;
        
        document.querySelectorAll('div, main, section').forEach(el => {
            let textLen = el.innerText ? el.innerText.trim().length : 0;
            let pCount = el.querySelectorAll('p').length;
            
            // Look for areas with paragraphs and substantial text
            if (textLen > 50 && pCount > 0) {
                let score = pCount * 100 + textLen;
                
                // Penalize root-level wrappers to find the tightest chat container
                if (el.tagName === 'MAIN' || el.tagName === 'BODY') {
                    score = score * 0.1;
                }
                if (textLen > document.body.innerText.length * 0.85) {
                    score = score * 0.5; 
                }
                
                // Bonus for ARIA roles often used in chat logs
                let role = el.getAttribute('role');
                if (role === 'log' || role === 'presentation' || role === 'region') {
                    score = score * 1.5;
                }
                
                if (score > maxScore) {
                    maxScore = score;
                    targetArea = el;
                }
            }
        });

        // Fallback if the scoring system fails
        if (!targetArea) {
            targetArea = document.querySelector('main') || document.body;
        }

        // 2. Use Selection API to extract clean, formatted text
        let selection = window.getSelection();
        let range = document.createRange();
        
        // Hide UI elements before copying to prevent junk text
        let btn = document.getElementById('nblm-export-btn');
        if (btn) btn.style.display = 'none';
        
        let junkSelectors = [
            '[aria-label*="emoji"]', 
            '[aria-label*="Recently used"]',
            'textarea', 
            'button' 
        ];
        
        let hiddenElements = [];
        junkSelectors.forEach(sel => {
            document.querySelectorAll(sel).forEach(el => {
                hiddenElements.push({ element: el, display: el.style.display });
                el.style.display = 'none';
            });
        });

        // Backup current user selection
        let originalRange = selection.rangeCount > 0 ? selection.getRangeAt(0) : null;
        
        // Execute copy selection
        selection.removeAllRanges();
        range.selectNodeContents(targetArea);
        selection.addRange(range);
        
        let rawText = selection.toString();
        
        // Restore user selection and UI visibility
        selection.removeAllRanges();
        if (originalRange) selection.addRange(originalRange);
        if (btn) btn.style.display = 'block';
        hiddenElements.forEach(item => {
            item.element.style.display = item.display;
        });

        if (!rawText || rawText.trim() === "") {
            alert("No text content found to export. Please ensure the chat is fully loaded.");
            return;
        }

        // 3. Filter out leftover known junk lines
        let lines = rawText.split('\n');
        let cleanLines = lines.filter(line => {
            let t = line.trim();
            return t !== 'Search results' && 
                   t !== 'No emoji found' && 
                   t !== 'Recently used' && 
                   t !== 'Loading';
        });

        // Reassemble and clean up multiple blank lines
        let markdownContent = cleanLines.join('\n')
            .replace(/\n{3,}/g, '\n\n')
            .trim();

        // 4. Download file
        let blob = new Blob([markdownContent], { type: 'text/markdown' });
        let url = window.URL.createObjectURL(blob);
        let a = document.createElement('a');
        
        let dateStr = new Date().toISOString().slice(0,10);
        
        a.style.display = 'none';
        a.href = url;
        a.download = 'NotebookLM_Chat_' + dateStr + '.md';
        
        document.body.appendChild(a);
        a.click();
        
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    }

    function createExportButton() {
        if (document.getElementById('nblm-export-btn')) return;

        let btn = document.createElement('button');
        btn.id = 'nblm-export-btn';
        btn.innerText = 'Export MD';
        
        btn.style.position = 'fixed';
        btn.style.bottom = '24px';
        btn.style.right = '24px';
        btn.style.zIndex = '999999';
        btn.style.padding = '12px 20px';
        btn.style.backgroundColor = '#1a73e8';
        btn.style.color = '#ffffff';
        btn.style.border = 'none';
        btn.style.borderRadius = '8px';
        btn.style.fontSize = '14px';
        btn.style.fontWeight = 'bold';
        btn.style.cursor = 'pointer';
        btn.style.boxShadow = '0 4px 6px rgba(0,0,0,0.1)';
        btn.style.transition = 'background-color 0.2s';

        btn.onmouseover = function() {
            btn.style.backgroundColor = '#1557b0';
        };
        btn.onmouseout = function() {
            btn.style.backgroundColor = '#1a73e8';
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
