
param(
    $login,
    $motdepasse
)

try {
    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = $False
    $excel.DisplayAlerts = $False

    $username = "admincreation@ueuromed.org"
    $password = ConvertTo-SecureString "@Dmin@@2024" -AsPlainText -Force
    $psCred = New-Object System.Management.Automation.PSCredential -ArgumentList ($username, $password)

    Import-Module MSOnline
    Connect-MsolService -Credential $psCred
    
    # Check if user exists first
    $user = Get-MsolUser -UserPrincipalName $login -ErrorAction SilentlyContinue
    if (-not $user) {
        Write-Output "ERROR: User $login not found"
        exit 1
    }

    # Reset password
    Set-MsolUserPassword –UserPrincipalName $login –NewPassword $motdepasse -ForceChangePassword $True
    Write-Output "SUCCESS: Password reset for $login"
}
catch {
    Write-Output "ERROR: $($_.Exception.Message)"
    exit 1
}
