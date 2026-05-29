from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.services.user import anonymize_user, delete_user_perman
from app.services.boards import delete_boards_perman
from app.services.files import delete_files_perman

scheduler = AsyncIOScheduler()

async def start_scheduler(db_pool):

    scheduler.add_job(anonymize_user, 'cron', minute = 0, args = [db_pool]),
    scheduler.add_job(delete_user_perman, 'corn', minute = 0, args = [db_pool])
    scheduler.add_job(delete_boards_perman, 'cron', minute = 0, args = [db_pool]),
    scheduler.add_job(delete_files_perman, 'cron', minute = 0, args = [db_pool])

    scheduler.start()

async def stop_scheduler():

    scheduler.shutdown()