import { useState } from "react";
import { Input } from "./components/ui/input";
import { Button } from "./components/ui/button";
import {
  Rocket,
  Loader2,
  CheckCircle2,
  ExternalLink,
  GitBranch,
} from "lucide-react";

function App() {
  const [repoUrl, setRepoUrl] = useState("");
  const [deployUrl, setDeployUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleDeploy = async () => {
    const trimmedUrl = repoUrl.trim();

    if (!trimmedUrl) {
      setError("Please enter a GitHub repository URL.");
      return;
    }

    setLoading(true);
    setError("");
    setDeployUrl("");

    try {
      // Step 1: Start deployment
      const response = await fetch("http://localhost:8000/api/deploy/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          repoUrl: trimmedUrl,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.error ||
            data.detail ||
            JSON.stringify(data) ||
            "Deployment failed.",
        );
      }

      const deployId = data.id;

      if (!deployId) {
        throw new Error("No deployment ID returned.");
      }

      // Step 2: Poll deployment status
      const maxAttempts = 120;
      const interval = 2000;

      for (let attempt = 0; attempt < maxAttempts; attempt++) {
        await new Promise((resolve) => setTimeout(resolve, interval));

        const statusResponse = await fetch(
          `http://localhost:8000/api/status/?id=${encodeURIComponent(deployId)}`,
        );

        if (!statusResponse.ok) {
          throw new Error("Unable to check deployment status.");
        }

        const statusData = await statusResponse.json();

        console.log("Deployment status:", statusData.status);

        if (statusData.status === "deployed") {
          const url = `http://${deployId}.localhost:8000/`;
          setDeployUrl(url);
          return;
        }

        if (statusData.status === "failed") {
          throw new Error("Deployment build failed.");
        }
      }

      throw new Error(
        "Deployment is still processing. Status check timed out.",
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-white px-5 py-12 text-gray-900">
      <div className="w-full max-w-lg">
        <div className="mb-8">
          <div className="mb-6 flex items-center gap-2">
            <GitBranch className="h-5 w-5 text-gray-700" />
            <span className="text-sm font-semibold tracking-tight">Deploy</span>
          </div>

          <h1 className="text-3xl font-semibold tracking-tight">
            Deploy your repository
          </h1>

          <p className="mt-3 text-sm leading-6 text-gray-500">
            Import a GitHub repository to build and deploy your application.
          </p>
        </div>

        <div className="space-y-4">
          <div className="space-y-2">
            <label
              htmlFor="repo-url"
              className="text-sm font-medium text-gray-800"
            >
              Git repository URL
            </label>

            <Input
              id="repo-url"
              type="url"
              placeholder="https://github.com/username/repository"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !loading) {
                  handleDeploy();
                }
              }}
              disabled={loading}
              className="h-11 border-gray-300 bg-white text-gray-900 placeholder:text-gray-400 focus-visible:ring-gray-400"
            />
          </div>

          <Button
            onClick={handleDeploy}
            disabled={loading || !repoUrl.trim()}
            className="h-11 w-full"
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Deploying...
              </>
            ) : (
              <>
                <Rocket className="mr-2 h-4 w-4" />
                Deploy
              </>
            )}
          </Button>

          {error && (
            <div
              role="alert"
              className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700"
            >
              {error}
            </div>
          )}

          {deployUrl && (
            <div className="rounded-md border border-gray-200 p-4">
              <div className="flex items-center gap-2 text-sm font-medium text-gray-900">
                <CheckCircle2 className="h-4 w-4 text-green-600" />
                Deployment successful
              </div>

              <p className="mt-2 text-sm text-gray-500">
                Your application is available at:
              </p>

              <a
                href={deployUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-2 flex items-center gap-2 break-all text-sm underline underline-offset-4"
              >
                {deployUrl}
                <ExternalLink className="h-4 w-4 shrink-0" />
              </a>

              <Button
                variant="outline"
                className="mt-4 w-full"
                onClick={() =>
                  window.open(deployUrl, "_blank", "noopener,noreferrer")
                }
              >
                Visit deployed website
                <ExternalLink className="ml-2 h-4 w-4" />
              </Button>
            </div>
          )}
        </div>

        <p className="mt-6 text-xs text-gray-400">
          Your repository will be built and deployed automatically.
        </p>
      </div>
    </main>
  );
}

export default App;
