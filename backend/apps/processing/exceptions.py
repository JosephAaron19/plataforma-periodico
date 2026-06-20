class TransientProcessingError(Exception):
    """
    Exception raised when a transient error occurs during PDF processing,
    indicating that the task can be retried with a new attempt ID.
    """
    def __init__(self, new_intento_id: int, attempt_number: int, original_exc: Exception):
        self.new_intento_id = new_intento_id
        self.attempt_number = attempt_number
        self.original_exc = original_exc
        super().__init__(str(original_exc))
