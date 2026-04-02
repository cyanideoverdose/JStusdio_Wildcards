import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

app.registerExtension({
    name: "JStudio.Wildcards",

    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name !== "JStudioWildcards") return;

        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            onNodeCreated?.apply(this, arguments);

            this.addWidget("button", "🔄 Refresh Wildcards", null, () => {
                api.fetchApi("/jstudio/reload_wildcards", {
                    method: "POST",
                })
                .then(r => r.json())
                .then(data => {
                    console.log("[JStudio Wildcards]", data.message);
                    app.extensionManager?.toast?.add?.({
                        severity: "success",
                        summary: "JStudio Wildcards",
                        detail: data.message,
                        life: 3000,
                    });
                    app.graph.setDirtyCanvas(true);
                })
                .catch(err => {
                    console.error("[JStudio Wildcards] Reload failed:", err);
                    app.extensionManager?.toast?.add?.({
                        severity: "error",
                        summary: "JStudio Wildcards",
                        detail: "Reload failed: " + err,
                        life: 4000,
                    });
                });
            });
        };
    },
});
