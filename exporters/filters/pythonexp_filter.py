from exporters.filters.base_filter import BaseFilter
from exporters.python_interpreter import Interpreter, create_context


class PythonexpFilter(BaseFilter):
    """
    Filter items depending on python expression.

        - python_expression (str)
            Python expression to filter by.
    """
    # List of options
    supported_options = {
        'python_expression': {'type': basestring}
    }

    def __init__(self, options):
        super(PythonexpFilter, self).__init__(options)
        self.expression = self.read_option('python_expression')
        self.interpreter = Interpreter()
        self.interpreter.check(self.expression)
        self.logger.info('PythonexpFilter has been initiated. Expression: {!r}'.format(self.expression))

    def filter(self, item):
        try:
            context = create_context()
            context.update({'item': item})
            return self.interpreter.eval(self.expression, context=context)
        except Exception as ex:
            self.logger.error(str(ex))
            raise
