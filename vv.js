// ==UserScript==
// @name         NotebookLM to Markdown Export (V4 - Mobile/Desktop Bulletproof)
// @namespace    http://tampermonkey.net/
// @version      4.0
// @description  Robust Markdown export ignoring hidden UI and mobile overlays.
// @match        https://notebooklm.google.com/*
// @grant        none
// ==/UserScript==

(function() {
    'use strict';

    function parseDOMToMarkdown(node) {
        if (node.nodeType === Node.TEXT_NODE) {
            return node.textContent;
        }

        if (node.nodeType !== Node.ELEMENT_NODE) {
            return "";
        }

        // 1. Skip strictly hidden elements (Critical for Mobile/NotebookLM UI)
        let style = window.getComputedStyle(node);
        if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') {
            return "";
        }

        let tag = node.tagName.toLowerCase();
        
        // 2. Skip interactive and structural UI elements
        if (['button', 'textarea', 'nav', 'header', 'svg', 'script', 'style', 'input'].includes(tag)) {
            return "";
        }

        // 3. Skip known ARIA UI wrappers (Emoji pickers, etc.)
        let ariaLabel = (node.getAttribute('aria-label') || '').toLowerCase();
        if (ariaLabel.includes('emoji') || ariaLabel.includes('recently used') || ariaLabel.includes('search results')) {
            return "";
        }

        // 4. Recursively parse children
        let childrenMarkdown = "";
        for (let child of node.childNodes) {
            childrenMarkdown += parseDOMToMarkdown(child);
        }

        // 5. Convert HTML tags to Markdown syntax
        switch (tag) {
            case 'br': return '\n';
            case 'hr': return '\n---\n\n';
            case 'p': return '\n\n' + childrenMarkdown + '\n\n';
            case 'div': 
            case 'article':
            case 'section':
                if (childrenMarkdown.trim().length > 0) {
                    return '\n\n' + childrenMarkdown + '\n\n';
                }
                return childrenMarkdown;
            case 'h1': return '\n\n# ' + childrenMarkdown + '\n\n';
            case 'h2': return '\n\n## ' + childrenMarkdown + '\n\n';
            case 'h3': return '\n\n### ' + childrenMarkdown + '\n\n';
            case 'h4': return '\n\n#### ' + childrenMarkdown + '\n\n';
            case 'h5': return '\n\n##### ' + childrenMarkdown + '\n\n';
            case 'h6': return '\n\n###### ' + childrenMarkdown + '\n\n';
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
            default: return childrenMarkdown;
        }
    }

    function cleanMarkdown(md) {
        let lines = md.split('\n');
        
        // Exact matches for leftover UI text that aren't caught by element tags
        let junkTexts = [
            'Sources', 'Chat', 'Studio', 
            'Start typing...', 'Save to note', 
            'No emoji found', 'Recently used', 
            'Search results', 'Loading',
            '1 source', 'sources', 'PLUS'
        ];
        
        let cleanLines = lines.filter(line => {
            let t = line.trim();
            if (t === '') return true; 
            if (junkTexts.includes(t)) return false;
            // Regex match for "X sources" floating text
            if (/^[0-9]+\s+source(s)?$/.test(t)) return false;
            // Regex match for standalone eye icon or similar floating single characters
            if (/^[\u2700-\u27BF]|[\uE000-\uF8FF]|\uD83C[\uDC00-\uDFFF]|\uD83D[\uDC00-\uDFFF]|[\u2011-\u26FF]|\uD83E[\uDD10-\uDDFF]$/.test(t)) return false;
            
            return true;
        });

        md = cleanLines.join('\n');
        
        // Fix up spacing
        md = md.replace(/\n{3,}/g, '\n\n'); 
        md = md.replace(/\*\* \*\*/g, '');  
        md = md.replace(/\* \*/g, '');      
        return md.trim();
    }

    function exportToMarkdown() {
        // Fallback safely to document.body so it works on any mobile DOM structure
        let targetArea = document.querySelector('div[role="log"]') || 
                         document.querySelector('main') || 
                         document.body;

        let rawMarkdown = parseDOMToMarkdown(targetArea);
        let finalMarkdown = cleanMarkdown(rawMarkdown);

        if (!finalMarkdown) {
            alert("No content found. Please make sure the chat is visible on your screen.");
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
        if (document.getElementById('nblm-export-btn')) return;

        let btn = document.createElement('button');
        btn.id = 'nblm-export-btn';
        btn.innerText = 'Export MD (V4)';
        
        btn.style.position = 'fixed';
        btn.style.bottom = '80px'; // Moved slightly higher for mobile view navigation bars
        btn.style.right = '24px';
        btn.style.zIndex = '999999';
        btn.style.padding = '12px 20px';
        btn.style.backgroundColor = '#8b5cf6'; // Purple button
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
        if (!document.getElementById('nblm-export-btn')) {
            createExportButton();
        }
    });

    observer.observe(document.body, { childList: true, subtree: true });
    createExportButton();

})();
