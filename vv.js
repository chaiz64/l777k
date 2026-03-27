// ==UserScript==
// @name         NotebookLM to Obsidian (V10 - Precision Formatter)
// @namespace    http://tampermonkey.net/
// @version      10.0
// @description  Strict structural fidelity matching the user's YAML and Dialogue prompt rules.
// @match        https://notebooklm.google.com/*
// @require      https://unpkg.com/turndown/dist/turndown.js
// @require      https://unpkg.com/turndown-plugin-gfm/dist/turndown-plugin-gfm.js
// @grant        none
// ==/UserScript==

(function() {
    'use strict';

    function sanitizeDOM(container) {
        let clone = container.cloneNode(true);

        let junkSelectors = [
            'button', 'textarea', 'input', 'nav', 'header', 'svg', 'img',
            '[role="button"]', '[role="toolbar"]', '[role="navigation"]', '[role="menu"]',
            '[aria-label*="emoji"]', '[aria-label*="Recently used"]',
            '.cdk-overlay-container', '[class*="tooltip"]', '[class*="icon"]',
            '.clip-board-button'
        ];
        junkSelectors.forEach(selector => {
            clone.querySelectorAll(selector).forEach(el => el.remove());
        });

        clone.querySelectorAll('pre, code, div').forEach(el => {
            let text = el.textContent || '';
            if (text.includes('task:') && text.includes('role:')) {
                el.remove();
            }
        });

        return clone;
    }

    function postProcessMarkdown(md) {
        // 1. Unescape Turndown characters
        md = md.replace(/\\=/g, '=');
        md = md.replace(/\\\*/g, '*');
        md = md.replace(/\\_/g, '_');
        md = md.replace(/\\\[/g, '[');
        md = md.replace(/\\\]/g, ']');
        md = md.replace(/\\-/g, '-');
        md = md.replace(/\\>/g, '>');

        // 2. Remove Turndown's automatic horizontal rules
        md = md.replace(/^-{3,}$/gm, '');
        md = md.replace(/^\*{3,}$/gm, '');

        // 3. Clean NotebookLM UI junk
        let lines = md.split('\n');
        let cleanLines = lines.filter(line => {
            let t = line.trim();
            if (t === '') return true;
            let bad = [
                'Search results', 'No emoji found', 'Recently used', 
                'Loading', 'Start typing...', 'Save to note',
                'Chat', 'Studio', 'Sources', 'PLUS', '👁️',
                'SourcesChatStudio', 'SourcesChat', 'ChatStudio'
            ];
            if (bad.includes(t)) return false;
            if (/^[0-9]+\s+source(s)?$/.test(t)) return false;
            if (/^(Today|Yesterday|[A-Za-z]+)\s•\s[0-9]{1,2}:[0-9]{2}\s(AM|PM)/i.test(t)) return false;
            return true;
        });
        md = cleanLines.join('\n');

        // 4. Reconstruct and force YAML Frontmatter spacing
        md = md.replace(/channel:\s*/g, '\n---\nchannel: ');
        md = md.replace(/title:\s*/g, '\ntitle: ');
        md = md.replace(/categories:\s*/g, '\ncategories: ');
        md = md.replace(/tags:\s*/g, '\ntags: ');
        md = md.replace(/speaker:\s*"(.*?)"/g, '\nspeaker: "$1"\n---\n\n');

        // 5. Force Dialogue formatting (e.g., **Host:**)
        md = md.replace(/(\*\*[A-Za-z0-9ก-๙\s]+:\*\*)/g, '\n\n$1\n\n');

        // 6. Enforce strict paragraph spacing
        let finalLines = md.split('\n').map(l => l.trim());
        let formattedMd = "";
        let inYaml = false;

        for (let i = 0; i < finalLines.length; i++) {
            let line = finalLines[i];
            if (line === '') continue;

            if (line === '---') {
                if (!inYaml) {
                    inYaml = true;
                    formattedMd += (i === 0 ? '' : '\n\n') + '---\n';
                } else {
                    inYaml = false;
                    formattedMd += '---\n\n';
                }
                continue;
            }

            if (inYaml) {
                formattedMd += line + '\n';
            } else {
                if (line.match(/^\*\*[^*]+:\*\*$/)) {
                    formattedMd += line + '\n\n'; // Dialogue name
                } else if (line.startsWith('#') || line.startsWith('>')) {
                    formattedMd += line + '\n\n'; // Headers and blockquotes
                } else if (line.startsWith('- ') || line.match(/^\d+\.\s/)) {
                    formattedMd += line + '\n';   // List items keep tight
                } else {
                    formattedMd += line + '\n\n'; // Normal paragraph
                }
            }
        }

        // Fix Highlighting bounds
        formattedMd = formattedMd.replace(/==\s+/g, '==');
        formattedMd = formattedMd.replace(/\s+==/g, '==');
        formattedMd = formattedMd.replace(/==(.*?)==/g, function(match, p1) {
             return '==' + p1.trim() + '==';
        });

        // Global cleanup for excessive newlines
        formattedMd = formattedMd.replace(/\n{3,}/g, '\n\n').trim();

        return formattedMd;
    }

    function triggerDownload(content) {
        let blob = new Blob([content], { type: 'text/markdown' });
        let url = window.URL.createObjectURL(blob);
        let a = document.createElement('a');
        
        let dateStr = new Date().toISOString().slice(0,10);
        let timeStr = new Date().toTimeString().slice(0,8).replace(/:/g, '');
        
        a.href = url;
        a.download = 'Interview_Translate_' + dateStr + '_' + timeStr + '.md';
        a.style.display = 'none';
        
        document.body.appendChild(a);
        a.click();
        
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    }

    function exportToMarkdown() {
        let btn = document.getElementById('nblm-export-v10-btn');
        let originalText = btn.innerText;
        btn.innerText = 'Formatting...';
        btn.style.backgroundColor = '#4338ca';

        try {
            if (typeof TurndownService === 'undefined') {
                throw new Error("Turndown library is not loaded.");
            }

            let bestContainer = document.querySelector('main') || document.body;
            let maxScore = -1;
            document.querySelectorAll('div, main, section').forEach(container => {
                if (container.tagName === 'BODY' || container.tagName === 'HTML') return;
                let pCount = container.querySelectorAll('p').length;
                let textLen = container.innerText ? container.innerText.trim().length : 0;
                let score = pCount * 100 + textLen;
                if (textLen > document.body.innerText.length * 0.9) score = score / 2;
                if (score > maxScore && pCount > 0) {
                    maxScore = score;
                    bestContainer = container;
                }
            });

            let cleanDOM = sanitizeDOM(bestContainer);

            let turndownService = new TurndownService({
                headingStyle: 'atx',
                codeBlockStyle: 'fenced',
                bulletListMarker: '-',
                strongDelimiter: '**',
                emDelimiter: '*'
            });
            
            if (typeof turndownPluginGfm !== 'undefined') {
                turndownService.use(turndownPluginGfm.gfm);
            }

            // Prevent turndown from escaping equals signs used for highlighting
            turndownService.escape = function(string) {
                return string;
            };

            let rawMarkdown = turndownService.turndown(cleanDOM.innerHTML);
            let finalMarkdown = postProcessMarkdown(rawMarkdown);

            if (!finalMarkdown || finalMarkdown === "") {
                throw new Error("No readable content found.");
            }

            triggerDownload(finalMarkdown);

            btn.innerText = 'Done!';
            btn.style.backgroundColor = '#10b981';
            setTimeout(() => {
                btn.innerText = originalText;
                btn.style.backgroundColor = '#312e81';
            }, 2000);

        } catch (error) {
            console.error("Export Error: ", error);
            alert("Export failed: " + error.message);
            btn.innerText = 'Error';
            btn.style.backgroundColor = '#ef4444';
            setTimeout(() => {
                btn.innerText = originalText;
                btn.style.backgroundColor = '#312e81';
            }, 2000);
        }
    }

    function createUI() {
        if (document.getElementById('nblm-export-v10-btn')) return;

        let btn = document.createElement('button');
        btn.id = 'nblm-export-v10-btn';
        btn.innerText = 'Export Obsidian (Strict)';
        
        btn.style.position = 'fixed';
        btn.style.bottom = '80px'; 
        btn.style.right = '24px';
        btn.style.zIndex = '999999';
        btn.style.padding = '14px 24px';
        btn.style.backgroundColor = '#312e81'; 
        btn.style.color = '#f8fafc';
        btn.style.border = '1px solid #4338ca';
        btn.style.borderRadius = '12px';
        btn.style.fontSize = '14px';
        btn.style.fontWeight = '600';
        btn.style.cursor = 'pointer';
        btn.style.boxShadow = '0 10px 15px -3px rgba(0, 0, 0, 0.5)';
        btn.style.transition = 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)';

        btn.onmouseover = function() {
            if (btn.innerText === 'Export Obsidian (Strict)') {
                btn.style.transform = 'translateY(-2px)';
                btn.style.backgroundColor = '#3730a3';
            }
        };
        btn.onmouseout = function() {
            if (btn.innerText === 'Export Obsidian (Strict)') {
                btn.style.transform = 'translateY(0)';
                btn.style.backgroundColor = '#312e81';
            }
        };

        btn.onclick = exportToMarkdown;
        document.body.appendChild(btn);
    }

    let observer = new MutationObserver(function() {
        if (!document.getElementById('nblm-export-v10-btn')) {
            createUI();
        }
    });

    observer.observe(document.body, { childList: true, subtree: true });
    setTimeout(createUI, 1000);

})();
