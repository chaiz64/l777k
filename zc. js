// ==UserScript==
// @name         NotebookLM to Markdown Export
// @namespace    http://tampermonkey.net/
// @version      1.0
// @description  Injects a floating button to export NotebookLM chat content to a Markdown file.
// @match        https://notebooklm.google.com/*
// @grant        none
// ==/UserScript==

(function() {
    'use strict';

    function exportToMarkdown() {
        let textContent = "";
        
        // Find all message containers. NotebookLM uses various nested divs. 
        // We target generic structural elements inside the main chat view.
        let contentArea = document.querySelector('main') || document.body;
        
        // Basic extraction (can be refined based on exact DOM structure)
        textContent = contentArea.innerText;

        if (!textContent || textContent.trim() === "") {
            alert("No text content found to export.");
            return;
        }

        // Basic formatting cleanup for Markdown
        let markdownContent = textContent
            .replace(/\n{3,}/g, '\n\n') // Reduce multiple newlines
            .trim();

        // Create Blob and trigger download
        let blob = new Blob([markdownContent], { type: 'text/markdown' });
        let url = window.URL.createObjectURL(blob);
        let a = document.createElement('a');
        
        a.style.display = 'none';
        a.href = url;
        a.download = 'NotebookLM_Export.md';
        
        document.body.appendChild(a);
        a.click();
        
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    }

    function createExportButton() {
        // Prevent duplicate buttons
        if (document.getElementById('nblm-export-btn')) return;

        let btn = document.createElement('button');
        btn.id = 'nblm-export-btn';
        btn.innerText = 'Export MD';
        
        // Button styling (Floating bottom right)
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

    // Use MutationObserver to ensure the button persists across React/Angular route changes
    let observer = new MutationObserver(function(mutations) {
        if (!document.getElementById('nblm-export-btn')) {
            createExportButton();
        }
    });

    observer.observe(document.body, { childList: true, subtree: true });

    // Initial creation attempt
    createExportButton();

})();
