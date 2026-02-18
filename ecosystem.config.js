module.exports = {
    apps: [
        {
            name: "ingress-leaderboard",
            script: "main.py",
            interpreter: "python3",
            cwd: ".", // Current directory
            env: {
                // Environment variables if needed
                // "BOT_TOKEN": "..." 
            },
            // Restart settings
            autorestart: true,
            watch: false,
            max_memory_restart: '200M'
        },
        // Future Bot Example (Uncomment to use)
        // {
        //   name: "another-bot",
        //   script: "../other-bot/main.py",
        //   interpreter: "python3", 
        // }
    ]
};
