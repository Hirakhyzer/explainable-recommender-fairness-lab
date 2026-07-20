function plot_recommender_metrics(outputDir)
%PLOT_RECOMMENDER_METRICS Plot synthetic recommender fairness outputs.
% Usage: plot_recommender_metrics('outputs')

if nargin < 1
    outputDir = 'outputs';
end

comparisonPath = fullfile(outputDir, 'results', 'synthetic_algorithm_comparison.csv');
fairnessPath = fullfile(outputDir, 'results', 'synthetic_exposure_fairness_audit.csv');
trustPath = fullfile(outputDir, 'results', 'synthetic_user_trust_audit.csv');

comparison = readtable(comparisonPath);
fairness = readtable(fairnessPath);
trust = readtable(trustPath);

figure;
bar(categorical(comparison.method), comparison.mean_relevance_proxy);
title('Mean relevance proxy by method');
ylabel('Relevance proxy');

figure;
meanGap = groupsummary(fairness, 'method', 'mean', 'absolute_exposure_gap');
bar(categorical(meanGap.method), meanGap.mean_absolute_exposure_gap);
title('Mean absolute exposure gap by method');
ylabel('Exposure gap');

figure;
meanTrust = groupsummary(trust, 'method', 'mean', 'trust_proxy_score');
bar(categorical(meanTrust.method), meanTrust.mean_trust_proxy_score);
title('Mean trust proxy by method');
ylabel('Trust proxy');
end
