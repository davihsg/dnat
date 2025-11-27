"use client";

import { useState, Suspense } from "react";
import {
  Box,
  Typography,
  Paper,
  Alert,
  Button,
  CircularProgress,
  Card,
  CardContent,
  Divider,
  Chip,
  TextField,
} from "@mui/material";
import { useAccount } from "wagmi";
import { useSearchParams } from "next/navigation";
import { useAsset } from "@/hooks/useContract";
import { requestExecution, ExecutionResult } from "@/services/executor";
import Link from "next/link";

function ExecuteContent() {
  const { address, isConnected } = useAccount();
  const searchParams = useSearchParams();
  
  const datasetId = searchParams.get("datasetId");
  const applicationId = searchParams.get("applicationId");

  const [isExecuting, setIsExecuting] = useState(false);
  const [result, setResult] = useState<ExecutionResult | null>(null);
  const [params, setParams] = useState("");

  const { data: dataset, isLoading: loadingDataset } = useAsset(
    datasetId ? BigInt(datasetId) : undefined
  );
  const { data: application, isLoading: loadingApplication } = useAsset(
    applicationId ? BigInt(applicationId) : undefined
  );

  const handleExecute = async () => {
    if (!address || !datasetId || !applicationId) return;

    setIsExecuting(true);
    setResult(null);

    try {
      const executionResult = await requestExecution({
        datasetId,
        applicationId,
        userAddress: address,
        params: params ? JSON.parse(params) : undefined,
      });
      setResult(executionResult);
    } catch (error) {
      setResult({
        success: false,
        error: error instanceof Error ? error.message : "Execution failed",
        timestamp: new Date().toISOString(),
      });
    } finally {
      setIsExecuting(false);
    }
  };

  if (!isConnected) {
    return (
      <Paper sx={{ p: 4 }}>
        <Alert severity="info">Please connect your wallet to execute</Alert>
      </Paper>
    );
  }

  if (!datasetId || !applicationId) {
    return (
      <Paper sx={{ p: 4 }}>
        <Alert severity="warning">
          Missing dataset or application ID. Please select from your access rights.
        </Alert>
        <Button component={Link} href="/my-access" sx={{ mt: 2 }}>
          Go to My Access Rights
        </Button>
      </Paper>
    );
  }

  const isLoading = loadingDataset || loadingApplication;

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Execute Application
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Run application over dataset in a secure SGX enclave
      </Typography>

      {isLoading ? (
        <Box sx={{ display: "flex", justifyContent: "center", p: 4 }}>
          <CircularProgress />
        </Box>
      ) : (
        <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>

          {/* Dataset Info */}
          <Card>
            <CardContent>
              <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 2 }}>
                <Chip label="Dataset" color="primary" size="small" />
                <Typography variant="h6">Dataset #{datasetId}</Typography>
              </Box>
              {dataset && (
                <>
                  <Typography variant="body2" color="text.secondary">
                    Owner: {dataset[1]}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Price: {dataset[5].toString()} Wei
                  </Typography>
                </>
              )}
            </CardContent>
          </Card>

          {/* Application Info */}
          <Card>
            <CardContent>
              <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 2 }}>
                <Chip label="Application" color="secondary" size="small" />
                <Typography variant="h6">Application #{applicationId}</Typography>
              </Box>
              {application && (
                <>
                  <Typography variant="body2" color="text.secondary">
                    Owner: {application[1]}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Price: {application[5].toString()} Wei
                  </Typography>
                </>
              )}
            </CardContent>
          </Card>

          {/* Parameters */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Execution Parameters (Optional)
              </Typography>
              <TextField
                fullWidth
                multiline
                rows={3}
                placeholder='{"epochs": 10, "learning_rate": 0.01}'
                value={params}
                onChange={(e) => setParams(e.target.value)}
                disabled={isExecuting}
              />
            </CardContent>
          </Card>

          {/* Execute Button */}
          <Button
            variant="contained"
            size="large"
            onClick={handleExecute}
            disabled={isExecuting}
            sx={{ py: 2 }}
          >
            {isExecuting ? (
              <>
                <CircularProgress size={24} sx={{ mr: 1 }} color="inherit" />
                Executing in SGX Enclave...
              </>
            ) : (
              "Execute"
            )}
          </Button>

          {/* Result */}
          {result && (
            <Card sx={{ bgcolor: result.success ? "success.dark" : "error.dark" }}>
              <CardContent>
                <Typography variant="h6" sx={{ color: "white", mb: 2 }}>
                  {result.success ? "✅ Execution Successful" : "❌ Execution Failed"}
                </Typography>
                <Divider sx={{ mb: 2, borderColor: "rgba(255,255,255,0.3)" }} />
                
                {result.output && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" sx={{ color: "rgba(255,255,255,0.7)" }}>
                      Output:
                    </Typography>
                    <Paper
                      sx={{
                        p: 2,
                        bgcolor: "rgba(0,0,0,0.3)",
                        fontFamily: "monospace",
                        whiteSpace: "pre-wrap",
                        color: "white",
                        maxHeight: 400,
                        overflow: "auto",
                      }}
                    >
                      {result.output}
                    </Paper>
                  </Box>
                )}

                {result.error && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" sx={{ color: "rgba(255,255,255,0.7)" }}>
                      Error:
                    </Typography>
                    <Typography sx={{ color: "white" }}>{result.error}</Typography>
                  </Box>
                )}

                {result.executionTime && (
                  <Typography variant="body2" sx={{ color: "rgba(255,255,255,0.7)" }}>
                    Execution time: {result.executionTime}ms
                  </Typography>
                )}

                <Typography variant="body2" sx={{ color: "rgba(255,255,255,0.5)", mt: 1 }}>
                  {result.timestamp}
                </Typography>
              </CardContent>
            </Card>
          )}
        </Box>
      )}
    </Box>
  );
}

export default function ExecutePage() {
  return (
    <Suspense
      fallback={
        <Box sx={{ display: "flex", justifyContent: "center", p: 4 }}>
          <CircularProgress />
        </Box>
      }
    >
      <ExecuteContent />
    </Suspense>
  );
}

