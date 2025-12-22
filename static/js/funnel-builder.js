/**
 * Samplit Funnel Builder
 * Native SVG/HTML implementation (No heavy libraries)
 */

function funnelBuilder() {
    return {
        nodes: [
            { id: 'start', x: 100, y: 300, label: 'Traffic Source', type: 'source' },
            { id: '1', x: 400, y: 300, label: 'Landing Page', type: 'page' }
        ],
        connections: [
            { id: 'c1', from: 'start', to: '1' }
        ],

        // State
        draggingNode: null,
        connectingNode: null,
        mouseX: 0,
        mouseY: 0,
        zoom: 1,
        pan: { x: 0, y: 0 },
        selectedNode: null,

        // Tools
        tools: [
            { type: 'page', label: 'Page', icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' },
            { type: 'action', label: 'Action', icon: 'M13 10V3L4 14h7v7l9-11h-7z' },
            { type: 'email', label: 'Email', icon: 'M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z' },
            { type: 'wait', label: 'Delay', icon: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z' }
        ],

        init() {
            // Dragging logic
            document.addEventListener('mousemove', (e) => this.onMouseMove(e));
            document.addEventListener('mouseup', (e) => this.onMouseUp(e));
        },

        // --- Node Operations ---

        addNode(type) {
            const id = 'node-' + Math.random().toString(36).substr(2, 9);
            this.nodes.push({
                id: id,
                x: 100 - this.pan.x, // Spawn near top-left visible
                y: 100 - this.pan.y,
                label: 'New ' + type,
                type: type
            });
        },

        deleteNode(id) {
            this.nodes = this.nodes.filter(n => n.id !== id);
            this.connections = this.connections.filter(c => c.from !== id && c.to !== id);
            this.selectedNode = null;
        },

        selectNode(node) {
            this.selectedNode = node;
        },

        // --- Dragging Logic ---

        startDrag(e, node) {
            e.preventDefault();
            this.draggingNode = node;
            this.selectedNode = node;

            // Calculate offset logic if needed, simple version for now
        },

        onMouseMove(e) {
            const rect = this.$refs.canvas.getBoundingClientRect();
            this.mouseX = (e.clientX - rect.left - this.pan.x) / this.zoom;
            this.mouseY = (e.clientY - rect.top - this.pan.y) / this.zoom;

            if (this.draggingNode) {
                this.draggingNode.x = this.mouseX;
                this.draggingNode.y = this.mouseY;
            }
        },

        onMouseUp(e) {
            this.draggingNode = null;

            if (this.connectingNode) {
                // Check if dropped on another node is handled by @mouseup on the node itself
                this.connectingNode = null;
            }
        },

        // --- Connection Logic ---

        startConnection(e, node) {
            e.stopPropagation();
            this.connectingNode = node;
        },

        completeConnection(e, targetNode) {
            e.stopPropagation();
            if (this.connectingNode && this.connectingNode.id !== targetNode.id) {
                // Check if connection exists
                const exists = this.connections.find(
                    c => c.from === this.connectingNode.id && c.to === targetNode.id
                );

                if (!exists) {
                    this.connections.push({
                        id: 'c-' + Math.random(),
                        from: this.connectingNode.id,
                        to: targetNode.id
                    });
                }
            }
            this.connectingNode = null;
        },

        // --- Visual Helpers ---

        getConnectorPath(conn) {
            const from = this.nodes.find(n => n.id === conn.from);
            const to = this.nodes.find(n => n.id === conn.to);
            if (!from || !to) return '';

            // Simple Bezier
            const dx = to.x - from.x;
            const ctrl1X = from.x + dx * 0.5;
            const ctrl1Y = from.y;
            const ctrl2X = to.x - dx * 0.5;
            const ctrl2Y = to.y;

            return `M ${from.x} ${from.y} C ${ctrl1X} ${ctrl1Y}, ${ctrl2X} ${ctrl2Y}, ${to.x} ${to.y}`;
        },

        getTempConnectionPath() {
            if (!this.connectingNode) return '';

            const from = this.connectingNode;
            const to = { x: this.mouseX, y: this.mouseY }; // Mouse position

            const dx = to.x - from.x;
            const ctrl1X = from.x + dx * 0.5;
            const ctrl1Y = from.y;
            const ctrl2X = to.x - dx * 0.5;
            const ctrl2Y = to.y;

            return `M ${from.x} ${from.y} C ${ctrl1X} ${ctrl1Y}, ${ctrl2X} ${ctrl2Y}, ${to.x} ${to.y}`;
        }
    }
}
