// Tiny ABI probe: compile against the assembled onnxrt_home headers, link the wheel's
// libonnxruntime, and ask the running library for its API version at runtime.
// If this builds and runs, the EP can be built against the same headers.
#include <cstdio>
#include <onnxruntime_c_api.h>

int main() {
  printf("compiled against ORT_API_VERSION = %d\n", ORT_API_VERSION);
  const OrtApiBase* base = OrtGetApiBase();
  printf("runtime build string             = %s\n", base->GetVersionString());
  const OrtApi* api = base->GetApi(ORT_API_VERSION);
  printf("runtime provides this API version: %s\n", api ? "yes" : "NO");
  return api ? 0 : 1;
}
