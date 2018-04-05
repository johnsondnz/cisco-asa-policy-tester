
from jinja2 import Environment, FileSystemLoader
from logzero import logger
from os import unlink
from os.path import isfile
from glob import glob


class GenerateReport(object):

    def __init__(self, context, script_dir, generated, reportname):

        self.script_dir = script_dir
        self.reportname = reportname if reportname != None else 'html_report'
        # self._cleanup()

        # setup the Jinja2 environment conditions
        file_loader = FileSystemLoader(
            '{}/jinja2_templates/'.format(script_dir))
        env = Environment(loader=file_loader,
                          trim_blocks=True, lstrip_blocks=True)

        # Render template and print generated config to console
        template = env.get_template('report.j2')
        HTML = template.render(context=context, generated=generated)
        with open('{}/reports/{}.html'.format(script_dir, self.reportname), 'w') as f:
            f.write(HTML)
        f.close()

        logger.info(
            'HTML report output to "{}/reports/{}.html"'.format(script_dir, self.reportname))

    # def _cleanup(self):
    #     '''
    #     Method to remove old reports based on flags
    #     '''

    #     if self.reportname == 'html_report':
    #         logger.debug('Cleaning up all previous reports')
    #         for report in glob(u'*.html'):
    #             filename = '{}/reports/{}'.format(self.script_dir, report)
    #             try:
    #                 if isfile(filename):
    #                     unlink(filename)
    #             except Exception:
    #                 logger.error('Unable to cleanup: {}'.format(filename))
    #                 pass
    #     else:
    #         cleanup = ['html_report.html', '{}.html'.format(self.reportname)]

    #         for report in cleanup:
    #             filename = '{}/reports/{}'.format(self.script_dir, report)
    #             try:
    #                 if isfile(filename):
    #                     unlink(filename)
    #             except Exception:
    #                 logger.error('Unable to cleanup: {}'.format(filename))
    #                 pass
