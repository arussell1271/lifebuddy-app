@{
    # Disable specific PSScriptAnalyzer rules for the repository.
    # See: https://github.com/PowerShell/PSScriptAnalyzer
    Rules = @{
        PSUseApprovedVerbs = @{ Enable = $false }
    }
}
