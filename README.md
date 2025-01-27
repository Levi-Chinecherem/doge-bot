
# **Doge Points Telegram Bot** 🐕

Welcome to the **Doge Points Telegram Bot**! This bot allows users to earn **Doge Points** by completing tasks, referring friends, and climbing the leaderboard. It’s a fun and gamified system designed to engage users and reward their participation.

---

## **Features**

- **Earn Doge Points**: Complete tasks and refer friends to earn points.
- **Task System**: Users can see and complete tasks to earn rewards.
- **Referral System**: Earn bonus points when your referrals complete tasks.
- **Leaderboard**: Compete with other users to become the **Top Doge**.
- **Admin Panel**: Add or remove tasks using simple commands.

---

## **Folder Structure**

```
doge_bot/
│
├── bot.py                # Main bot script
├── doge_world.db         # SQLite database (created automatically)
├── requirements.txt      # List of dependencies
├── Procfile              # Heroku deployment file
└── README.md             # Project documentation
```

---

## **Setup Instructions**

### **1. Prerequisites**

- Python 3.7 or higher.
- A Telegram bot token from [BotFather](https://core.telegram.org/bots#botfather).

### **2. Clone the Repository**

```bash
git clone https://github.com/Levi-Chinecherem/doge-bot.git
cd doge-bot
```

### **3. Install Dependencies**

```bash
pip install -r requirements.txt
```

### **4. Configure the Bot**

1. Replace `YOUR_TELEGRAM_BOT_TOKEN` in `bot.py` with your actual bot token.
2. (Optional) Set the token as an environment variable:
   ```bash
   export TOKEN=YOUR_TELEGRAM_BOT_TOKEN
   ```

### **5. Run the Bot Locally**

```bash
python bot.py
```

---

## **Deployment**

### **Option 1: Heroku**

1. **Create a Heroku Account**: Sign up at [heroku.com](https://www.heroku.com/).
2. **Install Heroku CLI**: Download from [here](https://devcenter.heroku.com/articles/heroku-cli).
3. **Login to Heroku**:
   ```bash
   heroku login
   ```
4. **Create a New Heroku App**:
   ```bash
   heroku create your-app-name
   ```
5. **Add a `Procfile`**:
   Create a `Procfile` with the following content:
   ```plaintext
   worker: python bot.py
   ```
6. **Deploy to Heroku**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git push heroku master
   ```
7. **Scale the Worker**:
   ```bash
   heroku ps:scale worker=1
   ```
8. **Set Your Bot Token**:
   ```bash
   heroku config:set TOKEN=YOUR_TELEGRAM_BOT_TOKEN
   ```

### **Option 2: PythonAnywhere**

1. **Create a PythonAnywhere Account**: Sign up at [pythonanywhere.com](https://www.pythonanywhere.com/).
2. **Upload Your Files**:
   - Upload `bot.py` and `requirements.txt` to your PythonAnywhere account.
3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Run the Bot**:
   ```bash
   python bot.py
   ```
5. **Keep the Bot Running**:
   - Use an **Always-On Task** to keep the bot running 24/7.

---

## **Usage**

### **User Commands**

- `/start`: Start the bot and see the welcome message.
- `/tasks`: View available tasks.
- `/leaderboard`: See the top 10 Doge Adventurers.
- `/referral`: Check who invited you.

### **Admin Commands**

- **Add a Task**:
  ```bash
  /addtask <name> <description> <doge_reward>
  ```
  Example:
  ```bash
  /addtask Follow us on Twitter Follow our Twitter account for updates 50
  ```

---

## **Example Workflow**

1. **User Joins**:
   - User sends `/start` and sees the welcome message.
2. **Complete Tasks**:
   - User sends `/tasks` and selects a task to complete.
   - After completing the task, they earn Doge Points.
3. **Check Leaderboard**:
   - User sends `/leaderboard` to see the top 10 users.
4. **Refer Friends**:
   - User shares their referral link (`/start <user_id>`) and earns points when friends join and complete tasks.

---

## **Troubleshooting**

- **Bot Not Responding**: Check the logs on your hosting platform for errors.
- **Database Issues**: Ensure the `doge_world.db` file is accessible and has the correct permissions.

---

## **Contributing**

Contributions are welcome! If you’d like to improve this project, please follow these steps:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/YourFeature`).
3. Commit your changes (`git commit -m 'Add some feature'`).
4. Push to the branch (`git push origin feature/YourFeature`).
5. Open a pull request.

---

## **License**

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## **Contact**

For questions or feedback, please reach out to:

- **Levi Chinecherem Chidi**: [mail me](mailto:lchinecherem2018@gmail.com)
- **Project Repository**: [GitHub Repo](https://github.com/Levi-Chinecherem/doge-bot)

---

Enjoy your adventure in **Doge World**! 🚀🐕

--- 