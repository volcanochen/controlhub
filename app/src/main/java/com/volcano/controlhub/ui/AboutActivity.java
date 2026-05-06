package com.volcano.controlhub.ui;

import com.volcano.controlhub.R;
import com.volcano.controlhub.BuildConfig;
import com.volcano.controlhub.AppInfo;
import android.os.Bundle;
import android.widget.Button;
import android.widget.TextView;
import androidx.appcompat.app.AppCompatActivity;

public class AboutActivity extends AppCompatActivity {
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_about);
        
        TextView versionText = findViewById(R.id.version_text);
        String versionName = "v" + AppInfo.APP_VERSION;
        String buildInfo = "版本：" + versionName + 
                          "\nCommit：" + BuildConfig.GIT_COMMIT_ID +
                          "\n构建时间：" + BuildConfig.BUILD_TIME;
        versionText.setText(buildInfo);
        
        TextView changelogText = findViewById(R.id.changelog_text);
        changelogText.setText(AppInfo.CHANGELOG);
        
        TextView copyrightText = findViewById(R.id.copyright_text);
        copyrightText.setText(AppInfo.APP_COPYRIGHT);
        
        Button backButton = findViewById(R.id.back_button);
        backButton.setOnClickListener(v -> {
            finish();
        });
    }
}
