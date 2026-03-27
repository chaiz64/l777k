// ==UserScript==
// @name         NotebookLM → Obsidian Export (V12)
// @namespace    http://tampermonkey.net/
// @version      12.0
// @description  Clean Obsidian markdown export with Smart Formatting for YAML, Headers, and Speakers.
// @match        https://notebooklm.google.com/*
// @grant        none
// ==/UserScript==

(function () {
    'use strict';

    // ── Configuration ────────────────────────────────────────────────────────
    const CONFIG = {
        buttonColor: '#7c3aed',
        fileNamePrefix: 'NotebookLM_Obsidian_'
    };

    // ── Core DOM to Markdown Converter ───────────────────────────────────────
    function parseNodeToMarkdown(node) {
        if (node.nodeType === Node.TEXT_NODE) {
            return node.textContent;
        }
        if (node.nodeType !== Node.ELEMENT_NODE) {
            return "";
        }

        const tag = node.tagName.toLowerCase();

        // Skip non-content tags
        if (['script', 'style', 'noscript', 'nav', 'button', 'svg', 'img', 'header', 'footer'].includes(tag)) {
            return "";
        }

        // Process children recursively
        let innerText = Array.from(node.childNodes).map(parseNodeToMarkdown).join("");

        // Format based on tag
        switch (tag) {
            case 'p':
            case 'div':
            case 'section':
                return `\n\n${innerText}\n\n`;
            case 'br':
                return `\n`;
            case 'h1':
                return `\n\n# ${innerText.trim()}\n\n`;
            case 'h2':
                return `\n\n## ${innerText.trim()}\n\n`;
            case 'h3':
                return `\n\n### ${innerText.trim()}\n\n`;
            case 'strong':
            case 'b':
                return `**${innerText.trim()}**`;
            case 'em':
            case 'i':
                return `*${innerText.trim()}*`;
            case 'li':
                return `\n- ${innerText.trim()}`;
            case 'blockquote':
                return `\n> ${innerText.trim()}\n`;
            default:
                return innerText;
        }
    }

    // ── Smart Text Formatting (The Magic for "Untitled 8" Format) ────────────
    function postProcessMarkdown(text) {
        // 1. Fix massive dashes into proper YAML boundary
        text = text.replace(/-{10,}/g, '---');

        // 2. Break YAML keys onto new lines
        const yamlKeys = ['channel:', 'title:', 'categories:', 'tags:', 'speaker:'];
        yamlKeys.forEach(key => {
            const regex = new RegExp(`(?<!\\n)(${key})`, 'g');
            text = text.replace(regex, '\n$1');
        });

        // 3. Close the YAML Frontmatter cleanly
        // Finds the last YAML key (speaker:) and ensures a closing '---' follows it before main content
        if (text.includes('---')) {
            text = text.replace(/(speaker:.*?)\n?(?=[^\s-])/i, '$1\n---\n\n');
        }

        // 4. Format Speakers (e.g., "Host:", "Guest (Isaac):") to be Bold and on their own line
        text = text.replace(/(\*?\*?(?:Host|Guest(?:\s*\([^)]+\))?)\*?\*?)\s*:/gi, '\n**$1:**\n');

        // 5. Ensure Headings have space around them
        text = text.replace(/([^\n])\n(##+ )/g, '$1\n\n$2');

        // 6. Clean up excessive whitespace and newlines (Max 2 newlines)
        text = text.replace(/ +/g, ' '); // collapse multiple spaces
        text = text.replace(/\n{3,}/g, '\n\n'); // collapse multiple newlines
        
        // 7. Fix blockquote spacing if user manually typed ">"
        text = text.replace(/\n>\s*/g, '\n\n> ');

        return text.trim();
    }

    // ── Main Execution Logic ─────────────────────────────────────────────────
    function runExport(btn) {
        btn.innerText = 'Extracting...';
        btn.style.backgroundColor = '#9333ea';

        setTimeout(() => {
            try {
                // Try to find the main content area (Note panel or Chat area)
                // Fallback: Use selected text if user highlights something
                let targetElement;
                const selection = window.getSelection();
                
                if (selection && selection.toString().trim().length > 0) {
                    // Extract from user selection
                    const container = document.createElement('div');
                    for (let i = 0; i < selection.rangeCount; i++) {
                        container.appendChild(selection.getRangeAt(i).cloneContents());
                    }
                    targetElement = container;
                } else {
                    // Auto-detect main note content (NotebookLM specific selectors)
                    // You might need to adjust this selector if NotebookLM updates their UI
                    const possibleContainers = document.querySelectorAll('[role="main"], article, .note-content-container, main');
                    targetElement = possibleContainers.length > 0 ? possibleContainers[possibleContainers.length - 1] : document.body;
                }

                // 1. Extract raw DOM to rough Markdown
                let rawMarkdown = parseNodeToMarkdown(targetElement);

                // 2. Post-process to fix YAML, Headers, and Speakers
                let cleanMarkdown = postProcessMarkdown(rawMarkdown);

                if (!cleanMarkdown || cleanMarkdown.length < 10) {
                    throw new Error("No meaningful content found to export.");
                }

                // 3. Trigger Download
                downloadFile(cleanMarkdown);
                
                btn.innerText = '✅ Success!';
                btn.style.backgroundColor = '#10b981'; // Green
            } catch (err) {
                console.error(err);
                btn.innerText = '❌ Failed';
                btn.style.backgroundColor = '#ef4444'; // Red
            }

            // Reset button
            setTimeout(() => {
                btn.innerText = 'Export to Obsidian';
                btn.style.backgroundColor = CONFIG.buttonColor;
            }, 3000);
        }, 100);
    }

    function downloadFile(content) {
        const dateStr = new Date().toISOString().split('T')[0];
        const fileName = `${CONFIG.fileNamePrefix}${dateStr}.md`;
        
        const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = fileName;
        document.body.appendChild(a);
        a.click();
        
        // Cleanup
        setTimeout(() => {
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }, 100);
    }

    // ── UI Generation ────────────────────────────────────────────────────────
    function createButton() {
        if (document.getElementById('nblm-v12')) return;

        const btn = document.createElement('button');
        btn.id = 'nblm-v12';
        btn.innerText = 'Export to Obsidian';
        
        Object.assign(btn.style, {
            position:                'fixed',
            bottom:                  '30px',
            right:                   '30px',
            zIndex:                  '999999',
            padding:                 '14px 20px',
            backgroundColor:         CONFIG.buttonColor,
            color:                   '#fff',
            border:                  'none',
            borderRadius:            '12px',
            fontSize:                '15px',
            fontWeight:              'bold',
            cursor:                  'pointer',
            boxShadow:               '0 4px 14px rgba(0,0,0,0.4)',
            transition:              'all 0.2s ease',
            minWidth:                '160px',
            fontFamily:              'sans-serif'
        });

        // Hover effects
        btn.onmouseover = () => btn.style.transform = 'translateY(-2px)';
        btn.onmouseout = () => btn.style.transform = 'translateY(0)';
        
        // Click action
        btn.onclick = () => runExport(btn);
        
        document.body.appendChild(btn);
    }

    // Initialize UI
    // Using MutationObserver to ensure button stays on page even if React re-renders
    const observer = new MutationObserver(() => {
        if (!document.getElementById('nblm-v12')) {
            createButton();
        }
    });
    
    observer.observe(document.body, { childList: true, subtree: true });
    
    // Initial render
    createButton();

})();

