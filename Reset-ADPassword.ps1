param(
    [string]$login,
    [string]$motdepasse
)

# Vérifier si les paramètres sont spécifiés
if (-not $login -or -not $motdepasse) {
    Write-Host "ERROR: Usage: Reset-ADPassword.ps1 -login <Nom_utilisateur> -motdepasse <Nouveau_mot_de_passe>"
    exit 1
}

try {
    # Fixed username - removed the dash prefix
    $username1 = "UEMF\guichet"
    $password1 = ConvertTo-SecureString "Guichet@@" -AsPlainText -Force
    $psCred1 = New-Object System.Management.Automation.PSCredential -ArgumentList ($username1, $password1)

    Write-Host "INFO: Attempting to connect to domain controller..."

    # Exécuter la réinitialisation du mot de passe à distance
    $result = Invoke-Command -ComputerName MORSRV01N.uemf.ma -Credential $psCred1 -ScriptBlock {
        param (
            $login,
            $motdepasse
        )

        try {
            # Charger le module Active Directory
            Import-Module ActiveDirectory -ErrorAction Stop
            Write-Output "INFO: Active Directory module loaded successfully"

            # Vérifier si l'utilisateur existe
            $user = Get-ADUser -Identity $login -Properties PasswordNeverExpires -ErrorAction Stop
            Write-Output "INFO: User $login found in Active Directory"

            # Réinitialiser le mot de passe de l'utilisateur
            Set-ADAccountPassword -Identity $login -Reset -NewPassword (ConvertTo-SecureString -AsPlainText $motdepasse -Force) -ErrorAction Stop
            Write-Output "INFO: Password reset successfully"
            
            # Only set ChangePasswordAtLogon if PasswordNeverExpires is False
            if (-not $user.PasswordNeverExpires) {
                Set-ADUser -Identity $login -ChangePasswordAtLogon $true -ErrorAction Stop
                Write-Output "INFO: User will be required to change password at next logon"
            } else {
                Write-Output "INFO: PasswordNeverExpires is enabled - user will not be required to change password at next logon"
            }
            
            Write-Output "SUCCESS: Le mot de passe de l'utilisateur $login a été réinitialisé avec succès."
            
            return $true
            
        } catch {
            Write-Output "ERROR: Erreur lors de la réinitialisation du mot de passe: $($_.Exception.Message)"
            return $false
        }
    } -ArgumentList $login, $motdepasse -ErrorAction Stop

    # Show all output from remote command
    Write-Host "DEBUG: Remote command output:"
    $result | ForEach-Object { Write-Host "  $_" }

    # Vérifier le résultat
    if ($result -contains $true) {
        Write-Host "SUCCESS: Password reset operation completed"
        exit 0
    } else {
        Write-Host "ERROR: Password reset operation failed"
        exit 1
    }

} catch {
    Write-Host "ERROR: Connection failed: $($_.Exception.Message)"
    exit 1
}