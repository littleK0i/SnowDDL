from io import BytesIO
from hashlib import md5
from pathlib import Path

from snowddl.blueprint import StageBlueprint, StageFileBlueprint
from snowddl.error import SnowDDLExecuteError
from snowddl.resolver.abc_resolver import AbstractResolver, ResolveResult, ObjectType


class StageFileResolver(AbstractResolver):
    def get_object_type(self) -> ObjectType:
        return ObjectType.STAGE_FILE

    def get_existing_objects(self):
        existing_objects = {}

        for stage_bp in self.config.get_blueprints_by_type(StageBlueprint).values():
            if not stage_bp.upload_stage_files:
                continue

            try:
                cur = self.engine.execute_meta("LIST @{stage_name:i}", {
                    "stage_name": stage_bp.full_name,
                })
            except SnowDDLExecuteError as e:
                # Stage does not exist or not authorized
                # Skip this error during planning
                if e.snow_exc.errno == 2003:
                    continue
                else:
                    raise

            all_files = {}
            all_hashes = {}

            for r in cur:
                path = Path(r['name'])

                if path.suffix == '.md5':
                    all_hashes[path.with_suffix('').with_suffix('')] = path.suffixes[-2].lstrip('.')
                else:
                    all_files[path] = True

            for path in all_files:
                # Snowflake LIST commands adds stage name implicitly, which should be removed
                stage_path = f"/{path.relative_to(path.parts[0])}"
                full_name=f"{stage_bp.full_name}({stage_path})"

                # Snowflake LIST commands provides "md5" and "size", but it is not reliable due to encryption
                existing_objects[full_name] = {
                    "stage_name": stage_bp.full_name,
                    "stage_path": stage_path,
                    "original_md5": all_hashes.get(path, None),
                }

        return existing_objects

    def get_blueprints(self):
        return self.config.get_blueprints_by_type(StageFileBlueprint)

    def create_object(self, bp: StageFileBlueprint):
        self._upload_file(bp)
        self._upload_md5_marker(bp)

        return ResolveResult.CREATE

    def compare_object(self, bp: StageFileBlueprint, row: dict):
        if row['original_md5'] == self._md5_file(bp.local_path):
            return ResolveResult.NOCHANGE

        self._upload_file(bp)
        self._upload_md5_marker(bp)

        return ResolveResult.REPLACE

    def drop_object(self, row: dict):
        # One call deletes original file and MD5 marker in one go
        self.engine.execute_safe_ddl("REMOVE @{stage_name:i}{stage_path:r}", {
            "stage_name": row['stage_name'],
            "stage_path": row['stage_path'],
        })

        return ResolveResult.DROP

    def _upload_file(self, bp: StageFileBlueprint):
        self.engine.execute_safe_ddl("PUT {local_path} @{stage_name:i}{stage_target:r} PARALLEL=1 OVERWRITE=TRUE AUTO_COMPRESS=FALSE", {
            "local_path": f"file://{bp.local_path}",
            "stage_name": bp.stage_name,
            "stage_target": Path(bp.stage_path).parent,
        })

    def _upload_md5_marker(self, bp: StageFileBlueprint):
        # Placeholder path for PUT command, directory does not matter
        # Actual contents of marker pseudo-file is empty and come from zero-length BytesIO in file_stream
        md5_marker_path = Path(bp.local_path).name + f".{self._md5_file(bp.local_path)}.md5"

        self.engine.execute_safe_ddl("PUT {local_path} @{stage_name:i}{stage_target:r} PARALLEL=1 OVERWRITE=TRUE AUTO_COMPRESS=FALSE", {
            "local_path": f"file://{md5_marker_path}",
            "stage_name": bp.stage_name,
            "stage_target": Path(bp.stage_path).parent,
        }, file_stream=BytesIO())

    def _md5_file(self, local_path: str):
        hash_md5 = md5()

        with open(local_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)

        return hash_md5.hexdigest()

    def destroy(self):
        # No need to delete stage files explicitly, files are destroyed automatically when stage is gone
        pass
