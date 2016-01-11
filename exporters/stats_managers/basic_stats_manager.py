from exporters.stats_managers.base_stats_manager import BaseStatsManager


class BasicStatsManager(BaseStatsManager):
    """
    Module to be used when no stats tracking is needed. It does nothing for iteration
    reports, and only prints a debug log message with final stats
    """

    def iteration_report(self, times, stats):
        pass

    def final_report(self, stats):
        self.logger.debug(repr(stats))
