import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

app.registerExtension({
    name: "JStudio.Wildcards",

    async beforeRegisterNodeDef(nodeType, nodeData, app) {

        // ── JStudio Wildcards node ──────────────────────────────────────
        if (nodeData.name === "JStudioWildcards") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                onNodeCreated?.apply(this, arguments);

                // Add a "Refresh Wildcards" button widget
                this.addWidget("button", "🔄 Refresh Wildcards", null, () => {
                    // Find the wildcards_folder value from this node's widgets
                    const folderWidget = this.widgets.find(w => w.name === "wildcards_folder");
                    const folder = folderWidget ? folderWidget.value : "";

                    api.fetchApi("/jstudio/reload_wildcards", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ wildcards_folder: folder }),
                    })
                    .then(r => r.json())
                    .then(data => {
                        console.log("[JStudio Wildcards]", data.message);
                        // Show a brief toast-style status on the node
                        const statusWidget = this.widgets.find(w => w.name === "_reload_status");
                        if (statusWidget) {
                            statusWidget.value = data.message;
                        }
                        app.graph.setDirtyCanvas(true);
                    })
                    .catch(err => {
                        console.error("[JStudio Wildcards] Reload failed:", err);
                    });
                });

                // Hidden status label
                this.addWidget("text", "_reload_status", "", null, { multiline: false });
            };

            // Resize node to fit the extra widgets
            const onResize = nodeType.prototype.onResize;
            nodeType.prototype.onResize = function (size) {
                onResize?.apply(this, arguments);
                size[1] = Math.max(size[1], 260);
                return size;
            };
        }

        // ── JStudio Reload node ─────────────────────────────────────────
        if (nodeData.name === "JStudioWildcardsReload") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                onNodeCreated?.apply(this, arguments);

                this.addWidget("button", "🔄 Reload Now", null, () => {
                    const folderWidget = this.widgets.find(w => w.name === "wildcards_folder");
                    const folder = folderWidget ? folderWidget.value : "";

                    api.fetchApi("/jstudio/reload_wildcards", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ wildcards_folder: folder }),
                    })
                    .then(r => r.json())
                    .then(data => {
                        console.log("[JStudio Wildcards]", data.message);
                        app.graph.setDirtyCanvas(true);
                    })
                    .catch(err => {
                        console.error("[JStudio Wildcards] Reload failed:", err);
                    });
                });
            };
        }
    },
});
