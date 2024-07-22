module.exports = {
  apps: [
      {
          name: 'chatbot',
          script: '/home/FututelBots/newBots2/venv/bin/gunicorn',
          args: 'chatbot:app -b 0.0.0.0:5000 --workers 3',
          interpreter: 'none',
          watch: false,
          env: {
              PYTHONUNBUFFERED: '1'
          }
      }
  ]
};
