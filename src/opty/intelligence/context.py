class ContextBase:
  def dispose(self):
    pass

  def __enter__(self):
    return self

  def __exit__(self, exc_type: type | None, exc_val: BaseException | None, exc_tb: object) -> None:
    self.dispose()
    return False
