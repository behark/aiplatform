const http = require('http');
const fs = require('fs');
const path = require('path');

// Create a simple HTML interface
const htmlContent = `
<!DOCTYPE html>
<html>
<head>
    <title>Sovereign Agent Platform</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; line-height: 1.6; }
        .container { max-width: 800px; margin: 0 auto; }
        h1 { color: #333; }
        .api-box { background: #f4f4f4; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .button { display: inline-block; background: #4CAF50; color: white; padding: 10px 15px;
                 text-decoration: none; border-radius: 4px; margin-right: 10px; }
        pre { background: #f8f8f8; padding: 10px; border-left: 3px solid #4CAF50; overflow-x: auto; }
        #response { background: #f0f0f0; padding: 15px; border-radius: 5px; min-height: 100px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Sovereign Agent Platform</h1>
        <p>This is a simple frontend to interact with your Sovereign Agent backend.</p>

        <div class="api-box">
            <h2>Backend API</h2>
            <p>Your backend is running at: <a href="http://localhost:8000" target="_blank">http://localhost:8000</a></p>

            <h3>Test API Connection</h3>
            <button id="testButton" class="button">Test Connection</button>

            <h3>API Response:</h3>
            <div id="response">Click the button above to test the connection...</div>
        </div>
    </div>

    <script>
        document.getElementById('testButton').addEventListener('click', async () => {
            const responseElem = document.getElementById('response');
            responseElem.innerHTML = 'Connecting to backend...';

            try {
                const response = await fetch('http://localhost:8000/');
                const data = await response.text();
                responseElem.innerHTML = `<pre>${data}</pre>`;
            } catch (error) {
                responseElem.innerHTML = `<pre>Error connecting to backend: ${error.message}</pre>`;
            }
        });
    </script>
</body>
</html>
`;

const server = http.createServer((req, res) => {
    if (req.url === '/') {
        res.writeHead(200, { 'Content-Type': 'text/html' });
        res.end(htmlContent);
    } else {
        res.writeHead(404);
        res.end('Not found');
    }
});

const PORT = 8080;
server.listen(PORT, () => {
    console.log(`Simple frontend running at http://localhost:${PORT}`);
});
