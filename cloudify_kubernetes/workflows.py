from cloudify.decorators import workflow
from cloudify.workflows import ctx

from fabric.api import env, run, settings
import json
import re

FORBIDDEN_CHARACTERS = '$!&`|><;#{}()'


def _prepare_kubectl_command(arguments):

    ctx.logger.debug('Input kubectl arguments: {0}'.format(arguments))

    command = 'kubectl {0}'.format(re.sub('[{0}]'.format(FORBIDDEN_CHARACTERS), '', arguments.replace('kubectl', '')))
    ctx.logger.debug('Kubectl command "{0}" will be executed'.format(command))

    return command


def _run_command(command, json_result=False):

    if json_result:
        command = '{0} -o json'.format(command)

    ctx.logger.info('Executing command "{0}" ...'.format(command))

    with settings(warn_only=True):
        result = run(command)
        ctx.logger.debug('Command execution result: {0}'.format(result))

        return {
            'successful': result.return_code == 0,
            'data_type': 'json' if json_result else 'text',
            'data': (json.loads(result) if json_result else result) if result.return_code == 0 else '',
            'error': result if not result.return_code == 0 else '',
            'return_code': result.return_code
        }


@workflow
def kubectl(kubectl_args, **kwargs):

    fabric_env = kwargs.get('fabric_env')

    env['key'] = fabric_env.get('key')
    env['user'] = fabric_env.get('user')
    env['host_string'] = fabric_env.get('host_string')

    command = _prepare_kubectl_command(kubectl_args)
    result = _run_command(command, True)

    if not result['successful']:
        result = _run_command(command, False)

    result_json = json.dumps(result)

    ctx.logger.info('Workflow execution result: {0}'.format(result_json))
