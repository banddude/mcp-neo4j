import importlib.util
import os
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import AsyncMock, Mock, patch

ROOT = Path(__file__).resolve().parents[1]


class RailwayStartupTests(unittest.IsolatedAsyncioTestCase):
    def load(self, environment=None, *, server_error=None, startup_error=None):
        self.driver = types.SimpleNamespace(close=AsyncMock())
        self.driver_factory = Mock(return_value=self.driver)
        self.server = types.SimpleNamespace(run_sse_async=AsyncMock(side_effect=server_error))
        self.create_server = Mock(return_value=self.server, side_effect=startup_error)
        neo4j = types.ModuleType('neo4j')
        neo4j.AsyncGraphDatabase = types.SimpleNamespace(driver=self.driver_factory)
        package = types.ModuleType('mcp_neo4j_cypher')
        package.__path__ = []
        server_module = types.ModuleType('mcp_neo4j_cypher.server')
        server_module.create_mcp_server = self.create_server
        self.enterContext(patch.dict(os.environ, environment or {}, clear=True))
        self.enterContext(patch.dict(sys.modules, {
            'neo4j': neo4j, 'mcp_neo4j_cypher': package,
            'mcp_neo4j_cypher.server': server_module,
        }))
        spec = importlib.util.spec_from_file_location('railway_fixture', ROOT / 'railway_sse_server.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    async def test_existing_defaults_and_normal_cleanup(self):
        module = self.load()
        await module.main()
        self.driver_factory.assert_called_once_with('bolt://localhost:7687', auth=('neo4j', 'password'))
        self.create_server.assert_called_once_with(self.driver, database='neo4j', namespace='', host='0.0.0.0', port=8000)
        self.server.run_sse_async.assert_awaited_once()
        self.driver.close.assert_awaited_once()

    async def test_url_host_and_railway_port_precedence(self):
        module = self.load({'NEO4J_URL':'bolt://url-fixture:7687', 'NEO4J_URI':'bolt://uri-fixture:7687',
                            'NEO4J_USERNAME':'fixture-user', 'NEO4J_PASSWORD':'fixture-password',
                            'NEO4J_DATABASE':'fixture-db', 'NEO4J_NAMESPACE':'fixture',
                            'NEO4J_MCP_SERVER_HOST':'127.0.0.1', 'PORT':'4567', 'NEO4J_MCP_SERVER_PORT':'9999'})
        await module.main()
        self.driver_factory.assert_called_once_with('bolt://url-fixture:7687', auth=('fixture-user', 'fixture-password'))
        self.create_server.assert_called_once_with(self.driver, database='fixture-db', namespace='fixture', host='127.0.0.1', port=4567)
        self.driver.close.assert_awaited_once()

    async def test_uri_and_secondary_port_remain_supported(self):
        module = self.load({'NEO4J_URL':'', 'NEO4J_URI':'bolt://fixture:7687', 'NEO4J_MCP_SERVER_PORT':'8123'})
        await module.main()
        self.assertEqual(self.driver_factory.call_args.args[0], 'bolt://fixture:7687')
        self.assertEqual(self.create_server.call_args.kwargs['port'], 8123)

    async def test_server_failure_closes_driver_and_propagates(self):
        module = self.load(server_error=RuntimeError('synthetic serve failure'))
        with self.assertRaisesRegex(RuntimeError, 'synthetic serve failure'):
            await module.main()
        self.driver.close.assert_awaited_once()

    async def test_startup_failure_also_closes_driver(self):
        module = self.load(startup_error=RuntimeError('synthetic startup failure'))
        with self.assertRaisesRegex(RuntimeError, 'synthetic startup failure'):
            await module.main()
        self.driver.close.assert_awaited_once()

    async def test_bad_port_fails_without_starting_server_and_closes_driver(self):
        module = self.load({'PORT':'not-a-port'})
        with self.assertRaises(ValueError):
            await module.main()
        self.create_server.assert_not_called()
        self.driver.close.assert_awaited_once()

    def test_nixpacks_uses_selected_python_to_install_requirements(self):
        import tomllib
        config = tomllib.loads((ROOT / 'nixpacks.toml').read_text())
        self.assertEqual(config['phases']['install']['cmds'], ['python -m pip install -r requirements.txt'])
        self.assertEqual(config['start']['cmd'], 'python railway_sse_server.py')


if __name__ == '__main__':
    unittest.main()
