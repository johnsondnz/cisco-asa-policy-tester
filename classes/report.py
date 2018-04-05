
from jinja2 import Environment, FileSystemLoader
from logzero import logger
from os import unlink


class GenerateReport(object):

    def __init__(self, context, script_dir, generated, reportname):

        reportname = reportname if reportname != None else 'html_report'

        cleanup = ['html_report.html', '{}.html'.format(reportname)]

        for report in cleanup:
            try:
                unlink('{}/reports/{}'.format(script_dir, report))
            except Exception:
                logger.error(
                    'Unable to cleanup: {}/reports/{}'.format(script_dir, report))
                pass

        # setup the Jinja2 environment conditions
        file_loader = FileSystemLoader(
            '{}/jinja2_templates/'.format(script_dir))
        env = Environment(loader=file_loader,
                          trim_blocks=True, lstrip_blocks=True)

        # Render template and print generated config to console
        template = env.get_template('report.j2')
        HTML = template.render(context=context, generated=generated)
        with open('{}/reports/{}.html'.format(script_dir, reportname), 'w') as f:
            f.write(HTML)
        f.close()

        logger.info(
            'HTML report output to "{}/reports/{}.html"'.format(script_dir, reportname))
