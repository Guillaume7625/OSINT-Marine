const { createPostgresStore } = require('../db/postgres-store');

async function run() {
  const connectionString = process.env.DATABASE_URL;
  const store = await createPostgresStore({ connectionString });
  await store.init();
  await store.close();
  // eslint-disable-next-line no-console
  console.log('Postgres schema initialized successfully.');
}

run().catch((error) => {
  // eslint-disable-next-line no-console
  console.error(error);
  process.exitCode = 1;
});
