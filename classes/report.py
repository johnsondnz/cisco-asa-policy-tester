
from jinja2 import Environment, FileSystemLoader
from logzero import logger

class GenerateReport(object):

    def __init__(self, context, script_dir, generated):
        # setup the Jinja2 environment conditions
        file_loader = FileSystemLoader('{}/jinja2_templates/'.format(script_dir))
        env = Environment(loader=file_loader, trim_blocks=True, lstrip_blocks=True)

        # Render template and print generated config to console
        template = env.get_template('report.j2')
        HTML = template.render(context=context, generated=generated)
        with open('{}/reports/html_report.html'.format(script_dir), 'w') as f:
            f.write(HTML)
        f.close()

        logger.info('HTML report output to "{}/reports/html_report.html"'.format(script_dir))
