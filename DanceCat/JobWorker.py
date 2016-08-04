"""
Docstring for DanceCat.JobWorker module.

This module contains the job's workers that will be
passed to the RQ worker to run in the background.
"""

from __future__ import print_function
import traceback
from flask_mail import Message
from StringIO import StringIO
from pyexcel.sheets import Sheet
from DanceCat.DatabaseConnector \
    import DatabaseConnector, DatabaseConnectorException
from .Helpers import Timer


def job_worker_send_mail(job, tracker_id, job_result, mailer):
    """Use to send email to user after job run success."""

    results_file = StringIO()

    results_file_data = [list(job_result['header'])]
    for row in job_result['rows']:
        results_file_data.append(list(row))

    Sheet(results_file_data).save_to_memory("xlsx", results_file)

    message = Message(
        "Job {job_name} ran successfully on DanceCat!".format(job_name=job.name),
        recipients=job.recipients,
        body="Dear users,\n\nPlease kindly notice that "
             "the job \"{job_name}\" ran successfully.\n"
             "We attached the result in this email "
             "for your later check.\n\n"
             "DanceCat.".format(job_name=job.name)
    )

    message.attach(
        "Result_tid_{tracker_id}.xlsx".format(tracker_id=tracker_id),
        content_type="application/"
                     "vnd.openxmlformats-officedocument."
                     "spreadsheetml.sheet",
        data=results_file.getvalue()
    )

    mailer.send(message)


def job_worker(job_id, tracker_id):
    """
    For now only focus on execute and save results to redis.

    :param job_id: Id of job that will be run.
    :param tracker_id: Job tracker id of tracking object.
    :return: query result.
    """

    timer = Timer()

    print(
        "Begin executing job {job_id} with tracker {tracker_id}".
        format(job_id=job_id, tracker_id=tracker_id)
    )

    from .Models import QueryDataJob, TrackJobRun
    from DanceCat import db, mail

    job = QueryDataJob.query.get(job_id)
    job.update_executed_times()

    tracker = TrackJobRun.query.get(tracker_id)
    tracker.start()
    db.session.commit()

    try:
        db_connector = DatabaseConnector(
            job.Connection.type,
            job.Connection.db_config_generator(),
            sql_data_style=False,
            dict_format=False,
            timeout=120
        )

        db_connector.connect()
        db_connector.execute(job.query_string)
        results = {
            'header': db_connector.columns_name,
            'rows': db_connector.fetch_all()
        }

        tracker.complete(
            is_success=True,
            run_duration=timer.get_total_milliseconds()
        )
        db.session.commit()

        if len(job.emails) > 0:
            job_worker_send_mail(job, tracker_id, results, mail)

        return results

    except DatabaseConnectorException as exception:
        tracker.complete(
            is_success=False,
            run_duration=timer.get_total_milliseconds(),
            error_string=exception.message
        )
        db.session.commit()

    except Exception as exception:
        tracker.complete(
            is_success=False,
            run_duration=timer.get_total_milliseconds(),
            error_string=str(exception) + "\n" + traceback.format_exc()
        )
        db.session.commit()

    return None
