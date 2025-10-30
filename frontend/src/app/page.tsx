"use client";
import React from "react";
import "@copilotkit/react-ui/styles.css";
import "./style.css";
import { CopilotKit, useCoAgentStateRender } from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";
import { useState } from "react";
import { useTheme } from "next-themes";

interface AgenticGenerativeUIProps {
    params: Promise<{
        integrationId: string;
    }>;
}

const AgenticGenerativeUI: React.FC<AgenticGenerativeUIProps> = ({ params }) => {
    const { integrationId } = React.use(params);
    return (
        <CopilotKit
            runtimeUrl={`/api/copilotkit/`}
            showDevConsole={true}
            // agent lock to the relevant agent
            agent="my_agent"
        >
            <Chat />
        </CopilotKit>
    );
};

interface AgentState {
    steps: {
        //description: string;       
        traceType: string;
        key: string;
        parentKey: string;
        timeCreated: number;
        timeFinished: number;
        elapsedTime: number;
        status: "pending" | "completed";

        tag: string;

        traceDetails: { key: string; value: string }[];

        usage: {
            modelName: string;
            inputTokenCount: number;
            outputTokenCount: number;
            inputCharCount: number;
            outputCharCount: number;
        };

    }[];
}

interface TraceDetailItemProps {
    detail: { key: string; value: string };
}

const TraceDetailItem: React.FC<TraceDetailItemProps> = ({ detail }) => {
    const [expanded, setExpanded] = useState(false);
    const value = detail.value?.trim() || '';
    const needsTruncation = value.split('\n').length >= 2 || value.length >= 100;

    return (
        <div>
            <span className="font-semibold">{detail.key}: </span>
            <pre
                className={`whitespace-pre-wrap transition-max-height`}
                style={{
                    maxHeight: expanded ? '1000px' : '3em', // line-clamp 2 高度大约 3em
                }}
            >
                {value}
            </pre>
            {needsTruncation && (
                <button
                    onClick={() => setExpanded(prev => !prev)}
                    className="text-blue-500 hover:underline text-xs"
                >
                    {expanded ? 'Show less' : 'Show more'}
                </button>
            )}
        </div>
    );
};

const Chat = () => {
    const { theme } = useTheme();

    // 展开状态记录，key是trace的唯一标识
    const [expandedKeys, setExpandedKeys] = useState<Record<string, boolean>>({});

    const toggleExpand = (key: string) => {
        setExpandedKeys((prev) => ({
            ...prev,
            [key]: !prev[key], // 切换当前 key 的展开/收起状态
        }));
    };


    useCoAgentStateRender<AgentState>({
        name: "my_agent",
        render: ({ state }) => {
            if (!state.steps || state.steps.length === 0) {
                return null;
            }

            const completedCount = state.steps.filter((step) => step.status === "completed").length;
            const progressPercentage = (completedCount / state.steps.length) * 100;



            return (
                <div className="flex">
                    <div
                        data-testid="task-progress"
                        className={`relative rounded-xl w-[700px] p-6 shadow-lg backdrop-blur-sm ${theme === "dark"
                            ? "bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white border border-slate-700/50 shadow-2xl"
                            : "bg-gradient-to-br from-white via-gray-50 to-white text-gray-800 border border-gray-200/80"
                            }`}
                    >
                        {/* Header */}
                        <div className="mb-5">
                            <div className="flex items-center justify-between mb-3">
                                <h3 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                                    Task Progress
                                </h3>
                                <div className={`text-sm ${theme === "dark" ? "text-slate-400" : "text-gray-500"}`}>
                                    {completedCount}/{state.steps.length} Complete
                                </div>
                            </div>

                            {/* Progress Bar */}
                            <div
                                className={`relative h-2 rounded-full overflow-hidden ${theme === "dark" ? "bg-slate-700" : "bg-gray-200"}`}
                            >
                                <div
                                    className="absolute top-0 left-0 h-full bg-gradient-to-r from-blue-500 to-purple-500 rounded-full transition-all duration-1000 ease-out"
                                    style={{ width: `${progressPercentage}%` }}
                                />
                                <div
                                    className={`absolute top-0 left-0 h-full w-full bg-gradient-to-r from-transparent to-transparent animate-pulse ${theme === "dark" ? "via-white/20" : "via-white/40"
                                        }`}
                                />
                            </div>
                        </div>

                        {/* Steps */}
                        <div className="space-y-2">
                            {state.steps.map((step, index) => {
                                const isCompleted = step.status === "completed";
                                const isCurrentPending =
                                    step.status === "pending" &&
                                    index === state.steps.findIndex((s) => s.status === "pending");
                                const isFuturePending = step.status === "pending" && !isCurrentPending;

                                return (
                                    <div
                                        key={index}
                                        className={`relative flex items-center p-2.5 rounded-lg transition-all duration-500 ${isCompleted
                                            ? theme === "dark"
                                                ? "bg-gradient-to-r from-green-900/30 to-emerald-900/20 border border-green-500/30"
                                                : "bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200/60"
                                            : isCurrentPending
                                                ? theme === "dark"
                                                    ? "bg-gradient-to-r from-blue-900/40 to-purple-900/30 border border-blue-500/50 shadow-lg shadow-blue-500/20"
                                                    : "bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200/60 shadow-md shadow-blue-200/50"
                                                : theme === "dark"
                                                    ? "bg-slate-800/50 border border-slate-600/30"
                                                    : "bg-gray-50/50 border border-gray-200/60"
                                            }`}
                                    >
                                        {/* Connector Line */}
                                        {index < state.steps.length - 1 && (
                                            <div
                                                className={`absolute left-5 top-full w-0.5 h-2 bg-gradient-to-b ${theme === "dark"
                                                    ? "from-slate-500 to-slate-600"
                                                    : "from-gray-300 to-gray-400"
                                                    }`}
                                            />
                                        )}

                                        {/* Status Icon */}
                                        <div
                                            className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center mr-2 ${isCompleted
                                                ? theme === "dark"
                                                    ? "bg-gradient-to-br from-green-500 to-emerald-600 shadow-lg shadow-green-500/30"
                                                    : "bg-gradient-to-br from-green-500 to-emerald-600 shadow-md shadow-green-200"
                                                : isCurrentPending
                                                    ? theme === "dark"
                                                        ? "bg-gradient-to-br from-blue-500 to-purple-600 shadow-lg shadow-blue-500/30"
                                                        : "bg-gradient-to-br from-blue-500 to-purple-600 shadow-md shadow-blue-200"
                                                    : theme === "dark"
                                                        ? "bg-slate-700 border border-slate-600"
                                                        : "bg-gray-300 border border-gray-400"
                                                }`}
                                        >
                                            {isCompleted ? (
                                                <CheckIcon />
                                            ) : isCurrentPending ? (
                                                <SpinnerIcon />
                                            ) : (
                                                <ClockIcon theme={theme} />
                                            )}
                                        </div>

                                        {/* Step Content */}
                                        <div className="flex-1 min-w-0">
                                            {/*
                      <div
                        data-testid="task-step-text"
                        className={`font-semibold transition-all duration-300 text-sm ${
                          isCompleted
                            ? theme === "dark"
                              ? "text-green-300"
                              : "text-green-700"
                            : isCurrentPending
                              ? theme === "dark"
                                ? "text-blue-300 text-base"
                                : "text-blue-700 text-base"
                              : theme === "dark"
                                ? "text-slate-400"
                                : "text-gray-500"
                        }`}
                      >
                        {step.description}
                      </div>
                      */}
                                            <div
                                                data-testid="task-step-container"
                                                className="rounded-lg p-3 mb-3 transition-all duration-300"
                                                style={{
                                                    backgroundColor: isCompleted
                                                        ? theme === "dark"
                                                            ? "#1f2937" // 深色完成背景
                                                            : "#ecfdf5" // 浅色完成背景
                                                        : theme === "dark"
                                                            ? "#111827"
                                                            : "#f9fafb"
                                                }}
                                            >
                                                {/* Step 标题 */}
                                                <div
                                                    data-testid="task-step-text"
                                                    className={`font-semibold transition-all duration-300 text-sm mb-2 ${isCompleted
                                                        ? theme === "dark"
                                                            ? "text-green-300"
                                                            : "text-green-700"
                                                        : isCurrentPending
                                                            ? theme === "dark"
                                                                ? "text-blue-300 text-base"
                                                                : "text-blue-700 text-base"
                                                            : theme === "dark"
                                                                ? "text-slate-400"
                                                                : "text-gray-500"
                                                        }`}
                                                >
                                                    {step.tag}
                                                </div>

                                                {/* Trace 信息展示 */}
                                                <div className="text-xs space-y-2">
                                                    {step.traceDetails?.map((detail, detailIndex) => {
                                                        return <TraceDetailItem key={detailIndex} detail={detail} />
                                                    })}
                                                    {step.usage && (
                                                        <div className="mt-1 text-xs text-gray-400">
                                                            <div className="grid grid-cols-[auto_1fr] gap-x-2">
                                                                {step.usage.modelName && (
                                                                    <>
                                                                        <span className="font-semibold">Model:</span><span>{step.usage.modelName}</span>
                                                                    </>
                                                                )}
                                                                <span className="font-semibold">Input:</span>
                                                                <div className="flex space-x-2">
                                                                    {step.usage.inputTokenCount && <span className="min-w-[100px]"><strong>{step.usage.inputTokenCount}</strong> tokens</span>}
                                                                    {step.usage.inputCharCount && <span><strong>{step.usage.inputCharCount}</strong> characters</span>}
                                                                </div>
                                                                <span className="font-semibold">Output:</span>
                                                                <div className="flex space-x-2">
                                                                    {step.usage.outputTokenCount && <span className="min-w-[100px]"><strong>{step.usage.outputTokenCount}</strong> tokens</span>}
                                                                    {step.usage.outputCharCount && <span><strong>{step.usage.outputCharCount}</strong> characters</span>}
                                                                </div>
                                                            </div>
                                                        </div>
                                                    )}
                                                </div>
                                            </div>

                                            {isCurrentPending && (
                                                <div
                                                    className={`text-sm mt-1 animate-pulse ${theme === "dark" ? "text-blue-400" : "text-blue-600"
                                                        }`}
                                                >
                                                    Processing...
                                                </div>
                                            )}
                                        </div>

                                        {/* Animated Background for Current Step */}
                                        {isCurrentPending && (
                                            <div
                                                className={`absolute inset-0 rounded-lg bg-gradient-to-r animate-pulse ${theme === "dark"
                                                    ? "from-blue-500/10 to-purple-500/10"
                                                    : "from-blue-100/50 to-purple-100/50"
                                                    }`}
                                            />
                                        )}
                                    </div>
                                );
                            })}
                        </div>

                        {/* Decorative Elements */}
                        <div
                            className={`absolute top-3 right-3 w-16 h-16 rounded-full blur-xl ${theme === "dark"
                                ? "bg-gradient-to-br from-blue-500/10 to-purple-500/10"
                                : "bg-gradient-to-br from-blue-200/30 to-purple-200/30"
                                }`}
                        />
                        <div
                            className={`absolute bottom-3 left-3 w-12 h-12 rounded-full blur-xl ${theme === "dark"
                                ? "bg-gradient-to-br from-green-500/10 to-emerald-500/10"
                                : "bg-gradient-to-br from-green-200/30 to-emerald-200/30"
                                }`}
                        />
                    </div>
                </div>
            );
        },
    });

    return (
        <div className="flex justify-center items-center h-full w-full">
            <div className="h-full w-full md:w-8/10 md:h-8/10 rounded-lg">
                <CopilotChat
                    className="h-full rounded-2xl max-w-6xl mx-auto"
                    labels={{
                        initial:
                            "Hi, I'm an agent! I can help you with anything you need and will show you progress as I work. What can I do for you?",
                    }}
                    suggestions={[
                        {
                            title: "RAG Tool: What is Exadata?",
                            message: "What is Exadata?",
                        },
                        {
                            title: "Function Tool: Get user information by user_id",
                            message: "Get information about a user by user_id=1",
                        },
                        {
                            title: "Function Tool: Get organization information by org_id",
                            message: "Get information about an organization by org_id=1",
                        },
                        
                    ]}
                />
            </div>
        </div>
    );
};

// Enhanced Icons
function CheckIcon() {
    return (
        <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
        </svg>
    );
}

function SpinnerIcon() {
    return (
        <svg
            className="w-4 h-4 animate-spin text-white"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
        >
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
        </svg>
    );
}

function ClockIcon({ theme }: { theme?: string }) {
    return (
        <svg
            className={`w-3 h-3 ${theme === "dark" ? "text-slate-400" : "text-gray-600"}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
        >
            <circle cx="12" cy="12" r="10" strokeWidth="2" />
            <polyline points="12,6 12,12 16,14" strokeWidth="2" />
        </svg>
    );
}

export default AgenticGenerativeUI;
