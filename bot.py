from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, CallbackContext
from telegram.ext import filters
from telegram.error import TimedOut, NetworkError, RetryAfter
import sqlite3
import asyncio
import nest_asyncio
import backoff
import logging
from typing import Optional
import shlex

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Enable nested event loops
nest_asyncio.apply()

# Replace with your bot token
TOKEN = '7480193735:AAHm8FihmOVjJ1oyUa7521Xgfbtg-7SGKoQ'

# Replace with your bot username
BOT_USERNAME = 'doge_adventurer_bot'

# Social account links
SOCIAL_LINKS = {
    'twitter': 'https://twitter.com/your_twitter',
    'telegram_channel': 'https://t.me/your_channel',
    'telegram_group': 'https://t.me/your_group',
    'discord': 'https://discord.gg/your_invite'
}

class DatabaseConnection:
    def __init__(self):
        self.conn = None
    
    def __enter__(self):
        self.conn = sqlite3.connect('doge_world.db')
        return self.conn
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.commit()
            self.conn.close()

class DogeBot:
    def __init__(self, token: str):
        self.token = token
        self.application = None

    @backoff.on_exception(
        backoff.expo,
        (TimedOut, NetworkError),
        max_tries=5,
        max_time=30
    )
    async def send_message_with_retry(self, message: str, chat_id: int, 
                                    parse_mode: Optional[str] = None,
                                    reply_markup: Optional[InlineKeyboardMarkup] = None) -> None:
        """Send a message with retry logic for network errors"""
        try:
            if self.application and self.application.bot:
                await self.application.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode=parse_mode,
                    reply_markup=reply_markup
                )
            else:
                logger.error("Application or bot not initialized")
        except RetryAfter as e:
            logger.warning(f"Rate limited. Waiting {e.retry_after} seconds")
            await asyncio.sleep(e.retry_after)
            return await self.send_message_with_retry(message, chat_id, parse_mode, reply_markup)
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            raise

    async def start(self, update: Update, context: CallbackContext) -> None:
        """Handle the /start command"""
        try:
            user_id = update.message.from_user.id
            username = update.message.from_user.username
            
            with DatabaseConnection() as conn:
                c = conn.cursor()
                
                # Check if user exists
                c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
                user = c.fetchone()
                
                if not user:
                    # Add new user with social_tasks_completed set to False
                    c.execute('INSERT INTO users (user_id, username, social_tasks_completed) VALUES (?, ?, ?)', 
                            (user_id, username, False))
                
                if context.args:
                    referrer_id = int(context.args[0])
                    c.execute('UPDATE users SET referred_by = ? WHERE user_id = ?', 
                            (referrer_id, user_id))
                
                # Check if social tasks are completed
                c.execute('SELECT social_tasks_completed FROM users WHERE user_id = ?', (user_id,))
                social_tasks_completed = c.fetchone()[0]
                
                if not social_tasks_completed:
                    # Show social task buttons
                    await self.show_social_tasks(update, context)
                    return
            
            # If social tasks are completed, show the main welcome message
            await self.show_main_welcome(update, context)
            
        except Exception as e:
            logger.error(f"Error in start command: {str(e)}")
            await self.send_message_with_retry(
                "Sorry, there was an error processing your command. Please try again later.",
                update.message.chat_id
            )

    async def show_social_tasks(self, update: Update, context: CallbackContext) -> None:
        """Show social task buttons for first-time users"""
        try:
            message = "👋 *Welcome to Doge World!* 🐕\n\n"
            message += "To start earning Doge Points, please join our social accounts:\n\n"
            message += "1. Follow us on Twitter\n"
            message += "2. Join our Telegram channel\n"
            message += "3. Join our Telegram group\n"
            message += "4. Join our Discord server\n\n"
            message += "Click the buttons below to join:"
            
            keyboard = [
                [InlineKeyboardButton("🐦 Follow us on Twitter", url=SOCIAL_LINKS['twitter'])],
                [InlineKeyboardButton("📢 Join our Telegram channel", url=SOCIAL_LINKS['telegram_channel'])],
                [InlineKeyboardButton("👥 Join our Telegram group", url=SOCIAL_LINKS['telegram_group'])],
                [InlineKeyboardButton("🎮 Join our Discord server", url=SOCIAL_LINKS['discord'])],
                [InlineKeyboardButton("✅ I've joined all", callback_data='social_tasks_completed')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await self.send_message_with_retry(
                message,
                update.message.chat_id,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Error in show_social_tasks: {str(e)}")
            await self.send_message_with_retry(
                "Sorry, there was an error displaying social tasks. Please try again later.",
                update.message.chat_id
            )

    async def handle_social_tasks_completion(self, update: Update, context: CallbackContext) -> None:
        """Handle the completion of social tasks"""
        try:
            query = update.callback_query
            await query.answer()
            
            user_id = query.from_user.id
            
            with DatabaseConnection() as conn:
                c = conn.cursor()
                c.execute('UPDATE users SET social_tasks_completed = ? WHERE user_id = ?', 
                        (True, user_id))
            
            # Send confirmation message
            await query.edit_message_text(
                "🎉 *Congratulations!* You've completed all social tasks!\n\n"
                "Preparing your Doge World adventure...",
                parse_mode='Markdown'
            )
            
            # Wait 1.5 seconds
            await asyncio.sleep(3.5)
            
            # Show the main welcome message
            await self.show_main_welcome(update, context)
            
        except Exception as e:
            logger.error(f"Error in handle_social_tasks_completion: {str(e)}")
            await self.send_message_with_retry(
                "Sorry, there was an error completing social tasks. Please try again later.",
                query.message.chat_id
            )

    # Also update the show_main_welcome method to handle message deletion
    async def show_main_welcome(self, update: Update, context: CallbackContext) -> None:
        """Show the main welcome message after social tasks are completed"""
        try:
            user_id = update.callback_query.from_user.id if update.callback_query else update.message.from_user.id
            chat_id = update.callback_query.message.chat_id if update.callback_query else update.message.chat_id
            
            # Delete the previous message if it exists
            if update.callback_query and update.callback_query.message:
                try:
                    await update.callback_query.message.delete()
                except Exception as e:
                    logger.warning(f"Could not delete previous message: {str(e)}")
            
            # Generate referral link
            referral_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
            
            # Main welcome message
            welcome_message = "🐕 *Welcome to Doge World!* 🐕\n\n"
            welcome_message += "You are now a **Doge Adventurer** on a quest to collect as many **Doge Points** as possible!\n\n"
            welcome_message += "🌟 *How to Earn Doge Points:*\n"
            welcome_message += "- Complete tasks to earn points.\n"
            welcome_message += "- Invite friends and earn points when they complete tasks.\n\n"
            welcome_message += f"🔗 *Your Referral Link:* `{referral_link}`\n"
            welcome_message += "Share this link with friends to earn bonus points!\n\n"
            welcome_message += "🏆 *Climb the Leaderboard* and become the **Top Doge**!\n\n"
            welcome_message += "Use the buttons below to get started:"
            
            # Main menu buttons
            keyboard = [
                [InlineKeyboardButton("📜 Tasks", callback_data='tasks')],
                [InlineKeyboardButton("🏆 Leaderboard", callback_data='leaderboard')],
                [InlineKeyboardButton("👤 Referral Info", callback_data='referral')],
                [InlineKeyboardButton("🔗 Get Referral Link", callback_data='referral_link')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await self.send_message_with_retry(
                welcome_message,
                chat_id,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Error in show_main_welcome: {str(e)}")
            await self.send_message_with_retry(
                "Sorry, there was an error displaying the welcome message. Please try again later.",
                chat_id
            )

    async def show_tasks(self, update: Update, context: CallbackContext) -> None:
        """Handle the /tasks command"""
        try:
            user_id = update.callback_query.from_user.id
            
            with DatabaseConnection() as conn:
                c = conn.cursor()
                c.execute('''SELECT * FROM tasks WHERE task_id NOT IN 
                           (SELECT task_id FROM completed_tasks WHERE user_id = ?)''', 
                         (user_id,))
                tasks = c.fetchall()
            
            if not tasks:
                await self.send_message_with_retry(
                    "No tasks available at the moment. Check back later!",
                    update.callback_query.message.chat_id
                )
                return
            
            keyboard = []
            for task in tasks:
                task_id, task_name, task_description, doge_reward = task
                button_text = f"{task_name} - {doge_reward} Doge Points"
                keyboard.append([InlineKeyboardButton(button_text, 
                                                    callback_data=f'task_{task_id}')])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await self.send_message_with_retry(
                "📜 *Available Tasks:*",
                update.callback_query.message.chat_id,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Error in show_tasks: {str(e)}")
            await self.send_message_with_retry(
                "Sorry, there was an error fetching tasks. Please try again later.",
                update.callback_query.message.chat_id
            )

    async def handle_task_completion(self, update: Update, context: CallbackContext) -> None:
        """Handle task completion callback queries"""
        try:
            query = update.callback_query
            await query.answer()
            
            user_id = query.from_user.id
            task_id = int(query.data.split('_')[1])
            
            with DatabaseConnection() as conn:
                c = conn.cursor()
                
                # Mark task as completed
                c.execute('INSERT INTO completed_tasks (user_id, task_id) VALUES (?, ?)',
                         (user_id, task_id))
                
                # Get task reward
                c.execute('SELECT doge_reward FROM tasks WHERE task_id = ?', (task_id,))
                doge_reward = c.fetchone()[0]
                
                # Update user points
                c.execute('UPDATE users SET doge_points = doge_points + ? WHERE user_id = ?',
                         (doge_reward, user_id))
                
                # Reward referrer if applicable
                c.execute('SELECT referred_by FROM users WHERE user_id = ?', (user_id,))
                referrer_id = c.fetchone()[0]
                if referrer_id:
                    c.execute('''UPDATE users SET doge_points = doge_points + ? 
                               WHERE user_id = ?''', (doge_reward // 2, referrer_id))
            
            await query.edit_message_text(
                f"🎉 *Task completed!* You earned {doge_reward} Doge Points! 🐕",
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error in handle_task_completion: {str(e)}")
            await query.edit_message_text(
                "Sorry, there was an error completing the task. Please try again."
            )

    async def show_leaderboard(self, update: Update, context: CallbackContext) -> None:
        """Handle the /leaderboard command"""
        try:
            with DatabaseConnection() as conn:
                c = conn.cursor()
                c.execute('''SELECT username, doge_points FROM users 
                           ORDER BY doge_points DESC LIMIT 10''')
                top_users = c.fetchall()
            
            leaderboard_message = "🏆 *Top 10 Doge Adventurers* 🏆\n\n"
            for i, (username, doge_points) in enumerate(top_users, start=1):
                leaderboard_message += f"{i}. {username}: {doge_points} Doge Points\n"
            
            await self.send_message_with_retry(
                leaderboard_message,
                update.callback_query.message.chat_id,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error in show_leaderboard: {str(e)}")
            await self.send_message_with_retry(
                "Sorry, there was an error fetching the leaderboard. Please try again later.",
                update.callback_query.message.chat_id
            )

    async def show_referral_info(self, update: Update, context: CallbackContext) -> None:
        """Handle the /referral command"""
        try:
            user_id = update.callback_query.from_user.id
            
            with DatabaseConnection() as conn:
                c = conn.cursor()
                c.execute('SELECT referred_by FROM users WHERE user_id = ?', (user_id,))
                referrer_id = c.fetchone()[0]
                
                if referrer_id:
                    c.execute('SELECT username FROM users WHERE user_id = ?', (referrer_id,))
                    referrer_username = c.fetchone()[0]
                    await self.send_message_with_retry(
                        f"👤 *You were invited by:* @{referrer_username}",
                        update.callback_query.message.chat_id,
                        parse_mode='Markdown'
                    )
                else:
                    await self.send_message_with_retry(
                        "You were not referred by anyone.",
                        update.callback_query.message.chat_id
                    )
                    
        except Exception as e:
            logger.error(f"Error in show_referral_info: {str(e)}")
            await self.send_message_with_retry(
                "Sorry, there was an error fetching referral information. Please try again later.",
                update.callback_query.message.chat_id
            )

    async def get_referral_link(self, update: Update, context: CallbackContext) -> None:
        """Handle the referral link button"""
        try:
            user_id = update.callback_query.from_user.id
            referral_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
            
            await update.callback_query.answer()
            await self.send_message_with_retry(
                f"🔗 *Your Referral Link:* `{referral_link}`\n\n"
                "Share this link with friends to earn bonus points!",
                update.callback_query.message.chat_id,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error in get_referral_link: {str(e)}")
            await self.send_message_with_retry(
                "Sorry, there was an error generating your referral link. Please try again later.",
                update.callback_query.message.chat_id
            )

    async def handle_main_menu(self, update: Update, context: CallbackContext) -> None:
        """Handle main menu button clicks"""
        try:
            query = update.callback_query
            await query.answer()
            
            if query.data == 'tasks':
                await self.show_tasks(update, context)
            elif query.data == 'leaderboard':
                await self.show_leaderboard(update, context)
            elif query.data == 'referral':
                await self.show_referral_info(update, context)
            elif query.data == 'referral_link':
                await self.get_referral_link(update, context)
                
        except Exception as e:
            logger.error(f"Error in handle_main_menu: {str(e)}")
            await self.send_message_with_retry(
                "Sorry, there was an error processing your request. Please try again later.",
                query.message.chat_id
            )

    async def add_task(self, update: Update, context: CallbackContext) -> None:
        """Handle the /addtask command (admin only)"""
        try:
            YOUR_ADMIN_USER_ID = 1878591152  # Replace with your actual admin user ID
            user_id = update.message.from_user.id
            
            # Check if the user is authorized
            if user_id != YOUR_ADMIN_USER_ID:
                await self.send_message_with_retry(
                    "You are not authorized to use this command.",
                    update.message.chat_id
                )
                return
            
            # Get the full command text
            command_text = update.message.text
            
            # Use shlex.split to handle quoted arguments properly
            try:
                args = shlex.split(command_text)[1:]  # Skip the command itself (/addtask)
            except ValueError as e:
                await self.send_message_with_retry(
                    "Invalid command format. Please check your quotes.",
                    update.message.chat_id
                )
                return
            
            # Check if the command has the correct number of arguments
            if len(args) < 3:
                await self.send_message_with_retry(
                    "Usage: /addtask <name> <description> <doge_reward>\n"
                    "Example: /addtask \"Begin Again\" \"Follow our Instagram account to earn points\" 50",
                    update.message.chat_id
                )
                return
            
            # Parse arguments
            task_name = args[0]
            task_description = " ".join(args[1:-1])  # Combine all arguments except the first and last
            try:
                doge_reward = int(args[-1])  # The last argument should be the reward
            except ValueError:
                await self.send_message_with_retry(
                    "Invalid doge_reward. Please provide a valid integer.",
                    update.message.chat_id
                )
                return
            
            # Insert the task into the database
            with DatabaseConnection() as conn:
                c = conn.cursor()
                c.execute('''INSERT INTO tasks (task_name, task_description, doge_reward) 
                        VALUES (?, ?, ?)''', (task_name, task_description, doge_reward))
            
            # Send confirmation message
            await self.send_message_with_retry(
                f"✅ *Task added successfully!*\n"
                f"Name: {task_name}\n"
                f"Description: {task_description}\n"
                f"Reward: {doge_reward} Doge Points",
                update.message.chat_id,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error in add_task: {str(e)}")
            await self.send_message_with_retry(
                "Sorry, there was an error adding the task. Please try again.",
                update.message.chat_id
            )


    async def error_handler(self, update: Update, context: CallbackContext) -> None:
        """Handle errors in the dispatcher"""
        logger.error(f"Exception while handling an update: {context.error}")
        
        if update and update.message:
            await self.send_message_with_retry(
                "Sorry, something went wrong. Please try again later.",
                update.message.chat_id
            )

    async def initialize(self) -> None:
        """Initialize the bot with error handling"""
        try:
            # Initialize application with custom request parameters
            self.application = (
                Application.builder()
                .token(self.token)
                .connect_timeout(30.0)
                .read_timeout(30.0)
                .write_timeout(30.0)
                .build()
            )
            
            # Add handlers in specific order
            self.application.add_handler(CommandHandler("start", self.start))
            self.application.add_handler(CommandHandler("addtask", self.add_task))
            
            # Add the social tasks completion handler BEFORE the general handlers
            self.application.add_handler(CallbackQueryHandler(
                self.handle_social_tasks_completion,
                pattern='^social_tasks_completed$'
            ))
            
            # Add other specific handlers
            self.application.add_handler(CallbackQueryHandler(
                self.handle_task_completion,
                pattern='^task_'
            ))
            
            # Add the general menu handler last
            self.application.add_handler(CallbackQueryHandler(self.handle_main_menu))
            
            # Add error handler
            self.application.add_error_handler(self.error_handler)
            
            return self.application
            
        except Exception as e:
            logger.error(f"Error initializing bot: {str(e)}")
            raise

    async def run(self) -> None:
        """Run the bot with error handling"""
        try:
            app = await self.initialize()
            await app.run_polling(
                poll_interval=1.0,        # Decrease polling interval
                timeout=30,               # Increase timeout
                drop_pending_updates=True # Ignore updates from when bot was offline
            )
        except Exception as e:
            logger.error(f"Error running bot: {str(e)}")
        finally:
            if self.application:
                await self.application.shutdown()
                
def init_db() -> None:
    """Initialize the database with required tables"""
    with DatabaseConnection() as conn:
        c = conn.cursor()
        
        # Users table
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            referred_by INTEGER,
            doge_points INTEGER DEFAULT 0,
            social_tasks_completed BOOLEAN DEFAULT FALSE
        )''')
        
        # Tasks table
        c.execute('''CREATE TABLE IF NOT EXISTS tasks (
            task_id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_name TEXT,
            task_description TEXT,
            doge_reward INTEGER
        )''')
        
        # Completed tasks table
        c.execute('''CREATE TABLE IF NOT EXISTS completed_tasks (
            user_id INTEGER,
            task_id INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(user_id),
            FOREIGN KEY(task_id) REFERENCES tasks(task_id),
            PRIMARY KEY (user_id, task_id)
        )''')
        
        # Create some initial tasks if the tasks table is empty
        c.execute('SELECT COUNT(*) FROM tasks')
        if c.fetchone()[0] == 0:
            initial_tasks = [
                ('Join Community', 'Join our Telegram community', 100),
                ('Share Invite', 'Share your referral link with friends', 50),
                ('Daily Check-in', 'Check in daily to earn points', 25),
                ('Complete Profile', 'Fill in your profile information', 75)
            ]
            c.executemany('INSERT INTO tasks (task_name, task_description, doge_reward) VALUES (?, ?, ?)',
                         initial_tasks)

async def main() -> None:
    """Main function to run the bot"""
    # Initialize database
    init_db()
    
    # Create and run bot
    bot = DogeBot(TOKEN)
    
    try:
        await bot.run()
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        if bot.application:
            await bot.application.shutdown()

if __name__ == "__main__":
    try:
        # Try running with default event loop
        asyncio.run(main())
    except RuntimeError as e:
        # If there's already a running event loop, create a new one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(main())
        except Exception as e:
            logger.error(f"Fatal error in main loop: {str(e)}")
        finally:
            loop.close()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")