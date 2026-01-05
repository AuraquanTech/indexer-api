const net = require('net');
const fs = require('fs');
const path = require('path');

const START_PORT = 3000;
const MAX_PORT = 3999;
const PORT_FILE = path.join(__dirname, '..', 'port_master.json');

/**
 * Checks if a port is available.
 * @param {number} port
 * @returns {Promise<boolean>}
 */
function isPortAvailable(port) {
    return new Promise((resolve) => {
        const server = net.createServer();

        server.listen(port, () => {
            server.close(() => {
                resolve(true);
            });
        });

        server.on('error', () => {
            resolve(false);
        });
    });
}

/**
 * Finds the first available port starting from startPort.
 * @param {number} startPort
 * @returns {Promise<number>}
 */
async function findAvailablePort(startPort) {
    for (let port = startPort; port <= MAX_PORT; port++) {
        if (await isPortAvailable(port)) {
            return port;
        }
    }
    throw new Error('No available ports found in range.');
}

async function main() {
    try {
        const port = await findAvailablePort(START_PORT);

        // Write to port_master.json
        const data = {
            port: port,
            last_updated: new Date().toISOString(),
            service: "indexer-frontend"
        };

        fs.writeFileSync(PORT_FILE, JSON.stringify(data, null, 2));

        // Output only the port number to stdout so the batch script can capture it
        console.log(port);
    } catch (error) {
        console.error('Error finding port:', error);
        process.exit(1);
    }
}

main();
