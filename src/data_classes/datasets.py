import logging
import os
from ..util import util
from .singletons import Paths
from dataclasses import dataclass, field
import random, string

@dataclass()
class DatasetDescription:
    _name: str
    _scheme: list
    _dependencies: list = field(default_factory=list)
    _path: str = field(init=False)
    
    def __post_init__(self):
        assert type(self._scheme) == list
        assert len(self._scheme) > 0
        
        paths = Paths.instance()
        datasets_path = paths.datasets
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        file_name = self._name + '_' + random_str  + '_.pkl'
        
        path = os.path.join(datasets_path, file_name)
        while os.path.isfile(path):
            random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
            file_name = self._name + '_' + random_str  + '_.pkl'
            path = os.path.join(datasets_path, file_name)
        
        self._path = path
    
    @property
    def name(self):
        return self._name
    
    @property
    def scheme(self):
        return self._scheme
    
    @property
    def path(self):
        return self._path
    
    @property
    def dependencies_exist(self):
        return len(self._dependencies) > 0
    
    @property
    def dependencies(self):
        # TODO REMOVE None
        return self._dependencies if self.dependencies_exist else None
    
    @dependencies.setter
    def dependencies(self, value):
        logging.warning('ADD DEPENDENCIES')
        self._dependencies = value
        pass
    
    def to_disk(self):
        util.write_pickle(self._path, self)
    
    def delete(self):
        util.remove_file(self.path)
               
    
    @staticmethod
    def from_disk(path):
        if util.is_non_zero_file(path):
            try: 
                dataset_description = util.read_pickle(path)
                dataset_description._path = path
                return dataset_description
            except:
                raise FileNotFoundError('Could not open {}'.format(path))