
from jinja2 import Environment, FileSystemLoader
from logzero import logger
from os import unlink
from os.path import isfile
from glob import glob


class GenerateReport(object):

    def __init__(self, context, script_dir, generated, reportname):

        self.context = context
        self.script_dir = script_dir
        self.generated = generated
        self.reportname = reportname if reportname != None else 'html_report'
        # self._cleanup()

    def gen_report(self):
        for interface, data in self.context.items():

            if interface != 'full_stats':

                # setup the Jinja2 environment conditions
                file_loader = FileSystemLoader(
                    '{}/jinja2_templates/'.format(self.script_dir))
                env = Environment(loader=file_loader,
                                trim_blocks=True, lstrip_blocks=True)

                # Render template and print generated config to console
                template = env.get_template('report.j2')
                filename = '{}/reports/{}.html'.format(self.script_dir, interface)
                HTML = template.render(context=self.context, generated=self.generated)
                with open(filename, 'w') as f:
                    f.write(HTML)
                f.close()

                logger.info(
                    'HTML report output to "{}"'.format(filename))

        # file_loader=FileSystemLoader(
        #     '{}/jinja2_templates/'.format(self.script_dir))
        # env=Environment(loader = file_loader,
        #                 trim_blocks = True, lstrip_blocks = True)

        # # Render template and print generated config to console
        # template=env.get_template('report.j2')
        # filename='{}/reports/{}.html'.format(self.script_dir, self.reportname)
        # HTML=template.render(context=self.context, generated=self.generated)
        # with open(filename, 'w') as f:
        #     f.write(HTML)
        # f.close()

        # logger.info(
        #     'HTML report output to "{}"'.format(filename))

    def cli_stats(self):

        '''
        Used to print the statistics to the cli
        '''
        for interface, data in self.context.items():

            if interface != 'full_stats':

                try:
                    print('\n')
                    logger.info('# ---------- {} STATS ---------- #'.format(interface))
                    logger.info('Total testlets: {}'.format(data['interface_stats']['total']))
                    logger.info('Total passed:   {}'.format(data['interface_stats']['pass']))
                    logger.info('Total failed:   {}'.format(data['interface_stats']['fail']))
                    logger.info('Total skipped:  {}'.format(data['interface_stats']['skip']))
                except Exception:
                    pass

        print('\n')
        logger.info('# ---------- FULL STATS ---------- #')
        logger.info('Total testlets: {}'.format(self.context['full_stats']['total']))
        logger.info('Total passed:   {}'.format(self.context['full_stats']['pass']))
        logger.info('Total failed:   {}'.format(self.context['full_stats']['fail']))
        logger.info('Total skipped:  {}'.format(self.context['full_stats']['skip']))


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
