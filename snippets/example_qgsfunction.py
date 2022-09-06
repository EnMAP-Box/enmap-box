from qgis.core import QgsExpressionFunction, QgsExpressionContext, QgsExpression


class MyFunction(QgsExpressionFunction):

    def __init__(self):
        super().__init__('myfunction', -1, 'MyGroup', 'Help Text')

    def func(self, values, context: QgsExpressionContext, parent, node):
        print(context.feature().isValid())
        return 42


# register function
func = MyFunction()
QgsExpression.registerFunction(func)

# use function
exp = QgsExpression('myfunction()')
context = QgsExpressionContext()
result = exp.evaluate(context)
print(f'Result {result}')
s = ""
