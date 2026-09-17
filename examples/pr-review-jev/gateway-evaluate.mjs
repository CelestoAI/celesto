// Fixed application helper; credentials stay in the environment, state arrives over stdin.
import { experimental_evaluate as evaluate } from 'ai';

let input = '';
for await (const chunk of process.stdin) input += chunk;
try {
  const request = JSON.parse(input);
  const started = performance.now();
  const result = await evaluate({
    model: 'typesafe-ai/jev', state: request.state, questions: request.questions,
    maxRetries: 0, abortSignal: AbortSignal.timeout(110_000),
  });
  const confidence = result.providerMetadata?.typesafe?.confidence ?? {};
  const answers = Object.fromEntries(Object.entries(result.answers).map(([id, answer]) => [
    id, { ...answer, ...(confidence[id] === undefined ? {} : { confidence: confidence[id] }) },
  ]));
  process.stdout.write(JSON.stringify({
    model: 'typesafe-ai/jev', answers, usage: result.usage,
    providerMetadata: result.providerMetadata,
    sdk_seconds: (performance.now() - started) / 1000,
  }));
} catch (error) {
  // SDK errors may contain headers. Never echo raw errors or requests.
  process.stderr.write(JSON.stringify({error: 'Gateway evaluation failed', status: error.statusCode ?? null}));
  process.exitCode = 1;
}
