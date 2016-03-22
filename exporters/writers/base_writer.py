import hashlib
from exporters.write_buffer import WriteBuffer
from exporters.logger.base_logger import WriterLogger
from exporters.pipeline.base_pipeline_item import BasePipelineItem


class ItemsLimitReached(Exception):
    """
    This exception is thrown when the desired items number has been reached
    """


class InconsistentWriteState(Exception):
    """
    This exception is thrown when write state is inconsistent with expected final state
    """


ITEMS_PER_BUFFER_WRITE = 500000
# Setting a default limit of 4Gb per file
SIZE_PER_BUFFER_WRITE = 4000000000


class BaseWriter(BasePipelineItem):
    """
    This module receives a batch and writes it where needed.
    """
    supported_options = {
        'items_per_buffer_write': {'type': int, 'default': ITEMS_PER_BUFFER_WRITE},
        'size_per_buffer_write': {'type': int, 'default': SIZE_PER_BUFFER_WRITE},
        'items_limit': {'type': int, 'default': 0},
        'check_consistency': {'type': bool, 'default': False}
    }

    def __init__(self, options, metadata, *args, **kwargs):
        super(BaseWriter, self).__init__(options, metadata, *args, **kwargs)
        self.finished = False
        self.check_options()
        self.items_limit = self.read_option('items_limit')
        self.logger = WriterLogger({'log_level': options.get('log_level'),
                                    'logger_name': options.get('logger_name')})
        self.export_formatter = kwargs.get('export_formatter')
        items_per_buffer_write = self.read_option('items_per_buffer_write')
        size_per_buffer_write = self.read_option('size_per_buffer_write')
        self.write_buffer = WriteBuffer(items_per_buffer_write, size_per_buffer_write, self.export_formatter)
        self.set_metadata('items_count', 0)

    def write(self, path, key):
        """
        Receive path to temp dump file and group key, and write it to the proper location.
        """
        raise NotImplementedError

    def write_batch(self, batch):
        """
        Receives the batch and writes it. This method is usually called from a manager.
        """
        for item in batch:
            self.write_buffer.buffer(item)
            key = self.write_buffer.get_key_from_item(item)
            if self.write_buffer.should_write_buffer(key):
                self._write(key)
            self.increment_written_items()
            self._check_items_limit()

    def _check_items_limit(self):
        """
        Check if a writer has reached the items limit. If so, it raises an ItemsLimitReached
        exception
        """
        if self.items_limit and self.items_limit == self.get_metadata('items_count'):
            raise ItemsLimitReached('Finishing job after items_limit reached:'
                                    ' {} items written.'.format(self.get_metadata('items_count')))

    def flush(self):
        """
        This method trigers a key write.
        """
        for key in self.grouping_info.keys():
            self._write(key)

    def close(self):
        """
        Called to clean all possible tmp files created during the process.
        """
        if self.write_buffer is not None:
            self.write_buffer.close()

    @property
    def grouping_info(self):
        if self.write_buffer is not None:
            return self.write_buffer.grouping_info
        else:
            return {}

    def _check_write_consistency(self):
        """
        This should be overwridden if a write consistency check is needed
        """
        self.logger.warning('Not checking write consistency')

    def increment_written_items(self):
        self.set_metadata('items_count', self.get_metadata('items_count') + 1)

    def _write(self, key):
        write_info = self.write_buffer.pack_buffer(key)
        self.write(write_info.get('compressed_path'), self.write_buffer.grouping_info[key]['membership'])
        self.write_buffer.clean_tmp_files(key, write_info.get('compressed_path'))

    def finish_writing(self):
        """
        Method called to do final writing operations before being closed
        """
        if self.read_option('check_consistency'):
            self._check_write_consistency()

    def set_metadata(self, key, value, module='writer'):
        super(BaseWriter, self).set_metadata(key, value, module)

    def update_metadata(self, data, module='writer'):
        super(BaseWriter, self).update_metadata(data, module)

    def get_metadata(self, key, module='writer'):
        return super(BaseWriter, self).get_metadata(key, module)

    def get_all_metadata(self, module='writer'):
        return super(BaseWriter, self).get_all_metadata(module)
