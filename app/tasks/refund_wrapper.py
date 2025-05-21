from .job_on_branch_tracking import mail_tracking_on_branch
from .job_on_road_tracking import mail_tracking_on_road


async def refund_wrapper():
    await mail_tracking_on_road()
    await mail_tracking_on_branch()
