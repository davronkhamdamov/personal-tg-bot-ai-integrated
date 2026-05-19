import os
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
import database as db
import claude_helper as claude

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hi! I'm your team planning bot powered by Claude.\n\n"
        "Commands:\n"
        "/plan — analyze recent discussion and generate a plan\n"
        "/addtask <description> — add a task (e.g. /addtask search feature for @john in 2 days)\n"
        "/tasks — view all tasks\n"
        "/done <id> — mark a task as complete\n\n"
        "I also record all messages in this chat to use as context for /plan."
    )


async def plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text("⏳ Analyzing discussion with Claude...")

    messages = db.get_recent_messages(chat_id)
    result = await asyncio.to_thread(claude.generate_plan, messages)

    await update.message.reply_text(result)


async def addtask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Usage: /addtask <description>\n"
            "Example: /addtask new search feature for @john needs to be done in 2 days"
        )
        return

    raw_text = " ".join(context.args)
    chat_id = update.effective_chat.id

    await update.message.reply_text("⏳ Parsing task with Claude...")

    parsed = await asyncio.to_thread(claude.parse_task, raw_text)

    task_id = db.add_task(
        chat_id=chat_id,
        description=parsed["description"],
        assignee=parsed.get("assignee"),
        deadline=parsed.get("deadline"),
    )

    assignee_str = f"@{parsed['assignee']}" if parsed.get("assignee") else "Unassigned"
    deadline_str = parsed["deadline"] if parsed.get("deadline") else "No deadline"

    await update.message.reply_text(
        f"✅ Task #{task_id} added!\n\n"
        f"📌 {parsed['description']}\n"
        f"👤 Assignee: {assignee_str}\n"
        f"📅 Deadline: {deadline_str}"
    )


async def tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    task_list = db.get_tasks(chat_id)

    if not task_list:
        await update.message.reply_text("No tasks yet. Use /addtask to add one.")
        return

    lines = ["📋 *Tasks:*\n"]
    for t in task_list:
        status_icon = "✅" if t["status"] == "done" else "🔲"
        assignee = f"@{t['assignee']}" if t["assignee"] else "Unassigned"
        deadline = t["deadline"] if t["deadline"] else "No deadline"
        lines.append(
            f"{status_icon} *#{t['id']}* {t['description']}\n"
            f"   👤 {assignee} | 📅 {deadline}"
        )

    await update.message.reply_text("\n\n".join(lines), parse_mode="Markdown")


async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Usage: /done <task_id>")
        return

    task_id = int(context.args[0])
    chat_id = update.effective_chat.id
    success = db.complete_task(task_id, chat_id)

    if success:
        await update.message.reply_text(f"✅ Task #{task_id} marked as done!")
    else:
        await update.message.reply_text(f"Task #{task_id} not found.")


async def record_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    chat_id = update.effective_chat.id
    username = update.effective_user.username or update.effective_user.first_name
    text = update.message.text

    db.save_message(chat_id, username, text)


def main():
    db.init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("plan", plan))
    app.add_handler(CommandHandler("addtask", addtask))
    app.add_handler(CommandHandler("tasks", tasks))
    app.add_handler(CommandHandler("done", done))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, record_message))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
