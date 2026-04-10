import inspect
import os

from RSPileScripting.RSPileModeler import RSPileModeler

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(lambda: None)))
RSPileModeler.startApplication(60044)

rspile_modeler = RSPileModeler(60044)
model = rspile_modeler.openFile(rf"{current_dir}\example_models\ExampleModel.rspile2")

model.close()
rspile_modeler.closeApplication()
