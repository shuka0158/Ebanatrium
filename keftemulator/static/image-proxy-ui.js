/**
 * Image Proxy UI Enhancement
 * Displays images fetched by the Image Proxy in Eba[Na]trium web UI
 */

(function() {
    'use strict';

    // Add styles for image display
    const style = document.createElement('style');
    style.textContent = `
        .node-images {
            margin-top: 8px;
            padding: 8px 0;
            border-top: 1px solid #262d38;
        }

        .node-images-label {
            font-size: 11px;
            color: #8892a2;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: .08em;
            margin-bottom: 8px;
        }

        .image-gallery {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
            gap: 8px;
        }

        .image-thumbnail {
            border: 1px solid #262d38;
            border-radius: 4px;
            overflow: hidden;
            cursor: pointer;
            transition: border-color 0.2s;
            background: #0d1014;
            aspect-ratio: 1;
        }

        .image-thumbnail:hover {
            border-color: #4fd1a5;
        }

        .image-thumbnail img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: block;
        }

        .image-modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.8);
            z-index: 10000;
            justify-content: center;
            align-items: center;
        }

        .image-modal.show {
            display: flex;
        }

        .image-modal-content {
            max-width: 80vw;
            max-height: 80vh;
            position: relative;
        }

        .image-modal img {
            max-width: 100%;
            max-height: 100%;
            border-radius: 4px;
        }

        .image-modal-close {
            position: absolute;
            top: 10px;
            right: 10px;
            background: rgba(0, 0, 0, 0.7);
            color: #d8dee8;
            border: none;
            width: 32px;
            height: 32px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 18px;
            line-height: 1;
        }

        .image-modal-close:hover {
            background: rgba(0, 0, 0, 0.9);
        }

        .image-fetch-status {
            font-size: 11px;
            color: #4fd1a5;
            margin-top: 4px;
        }
    `;
    document.head.appendChild(style);

    // Hook into the scan response to add image display
    const originalFetch = window.fetch;
    window.fetch = function(...args) {
        return originalFetch.apply(this, args).then(response => {
            // Check if this is a scan API call
            if (args[0] && args[0].toString().includes('/api/scans/')) {
                // Clone response so we can read it
                const clonedResponse = response.clone();

                clonedResponse.json().then(data => {
                    // Wait a moment for DOM to update, then enhance nodes with images
                    setTimeout(() => enhanceNodesWithImages(data), 100);
                }).catch(() => {
                    // Not JSON, ignore
                });
            }
            return response;
        });
    };

    function enhanceNodesWithImages(data) {
        if (!data.nodes) return;

        data.nodes.forEach(node => {
            if (!node.images || node.images.length === 0) return;

            // Find the node element in the DOM
            const nodeElements = document.querySelectorAll('[data-id]');
            let nodeElement = null;

            for (const el of nodeElements) {
                if (el.getAttribute('data-id') == node.id) {
                    nodeElement = el;
                    break;
                }
            }

            // If not found by data-id, try finding by text content
            if (!nodeElement) {
                for (const el of document.querySelectorAll('.node, [role="listitem"]')) {
                    if (el.textContent.includes(node.value || '')) {
                        nodeElement = el;
                        break;
                    }
                }
            }

            if (!nodeElement) return;

            // Check if images already added
            if (nodeElement.querySelector('.node-images')) return;

            // Create images container
            const imagesContainer = document.createElement('div');
            imagesContainer.className = 'node-images';

            const label = document.createElement('div');
            label.className = 'node-images-label';
            label.textContent = `📷 ${node.images.length} image${node.images.length > 1 ? 's' : ''}`;
            imagesContainer.appendChild(label);

            const gallery = document.createElement('div');
            gallery.className = 'image-gallery';

            node.images.forEach((imgUrl, idx) => {
                const thumbnail = document.createElement('div');
                thumbnail.className = 'image-thumbnail';

                const img = document.createElement('img');
                img.src = imgUrl;
                img.alt = `Image ${idx + 1}`;
                img.loading = 'lazy';
                img.onerror = function() {
                    this.style.display = 'none';
                };

                // Click to open full image
                img.style.cursor = 'pointer';
                img.onclick = function(e) {
                    e.stopPropagation();
                    showImageModal(imgUrl);
                };

                thumbnail.appendChild(img);
                gallery.appendChild(thumbnail);
            });

            imagesContainer.appendChild(gallery);

            // Add to node
            const lastElement = nodeElement.lastElementChild;
            if (lastElement) {
                lastElement.after(imagesContainer);
            } else {
                nodeElement.appendChild(imagesContainer);
            }

            console.log(`✅ Added ${node.images.length} images to node ${node.id}`);
        });
    }

    function showImageModal(imgUrl) {
        // Create modal
        const modal = document.createElement('div');
        modal.className = 'image-modal show';

        const content = document.createElement('div');
        content.className = 'image-modal-content';

        const img = document.createElement('img');
        img.src = imgUrl;
        img.alt = 'Full size image';

        const closeBtn = document.createElement('button');
        closeBtn.className = 'image-modal-close';
        closeBtn.textContent = '✕';
        closeBtn.onclick = function() {
            modal.remove();
        };

        content.appendChild(img);
        content.appendChild(closeBtn);
        modal.appendChild(content);

        // Close on background click
        modal.onclick = function(e) {
            if (e.target === modal) {
                modal.remove();
            }
        };

        document.body.appendChild(modal);
    }

    console.log('🖼️ Image Proxy UI enhancement loaded');
    console.log('📷 Images from proxy will be displayed in results');
})();
